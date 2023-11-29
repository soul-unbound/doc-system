from flask import Flask, render_template, request, redirect, url_for
import boto3
from botocore.exceptions import NoCredentialsError
import psycopg2

app = Flask(_name_)

# AWS S3 Configuration
S3_BUCKET = 'your-s3-bucket-name'

# RDS Configuration
RDS_HOST = 'your-rds-host'
RDS_PORT = 'your-rds-port'
RDS_DB = 'your-rds-database'
RDS_USER = 'your-rds-username'
RDS_PASSWORD = 'your-rds-password'

# AWS S3 and RDS clients
s3 = boto3.client('s3')
rds = psycopg2.connect(host=RDS_HOST, port=RDS_PORT, database=RDS_DB, user=RDS_USER, password=RDS_PASSWORD)

# Create a table in RDS for storing metadata
with rds.cursor() as cursor:
    cursor.execute("CREATE TABLE IF NOT EXISTS documents (id SERIAL PRIMARY KEY, filename VARCHAR, s3_key VARCHAR, file_type VARCHAR);")
rds.commit()

def generate_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('put_object',
                                                    Params={'Bucket': bucket_name, 'Key': object_name},
                                                    ExpiresIn=expiration)
    except NoCredentialsError:
        print('Credentials not available')
        return None

    return response

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']
    file_type = request.form.get('file_type')

    if file.filename == '' or not file_type:
        return redirect(request.url)

    # Generate a unique S3 key for the file
    s3_key = f"uploads/{file.filename}"

    # Generate a pre-signed URL
    presigned_url = generate_presigned_url(S3_BUCKET, s3_key)

    if presigned_url:
        # Upload file to S3 using the pre-signed URL
        with open(file.filename, 'rb') as data:
            requests.put(presigned_url, data=data)

        # Save metadata to RDS
        with rds.cursor() as cursor:
            cursor.execute("INSERT INTO documents (filename, s3_key, file_type) VALUES (%s, %s, %s);", (file.filename, s3_key, file_type))
        rds.commit()

    return redirect(url_for('index'))

if _name_ == '_main_':
    app.run(debug=True)
