from flask import Flask, render_template, request, redirect, url_for
import boto3
import psycopg2

app = Flask(__name__)

# AWS S3 Configuration
S3_BUCKET = 'your-s3-bucket-name'
S3_ACCESS_KEY = 'your-s3-access-key'
S3_SECRET_KEY = 'your-s3-secret-key'

# RDS Configuration
RDS_HOST = 'your-rds-host'
RDS_PORT = 'your-rds-port'
RDS_DB = 'your-rds-database'
RDS_USER = 'your-rds-username'
RDS_PASSWORD = 'your-rds-password'

# AWS S3 and RDS clients
s3 = boto3.client('s3', aws_access_key_id=S3_ACCESS_KEY, aws_secret_access_key=S3_SECRET_KEY)
rds = psycopg2.connect(host=RDS_HOST, port=RDS_PORT, database=RDS_DB, user=RDS_USER, password=RDS_PASSWORD)

# Create a table in RDS for storing metadata
with rds.cursor() as cursor:
    cursor.execute("CREATE TABLE IF NOT EXISTS documents (id SERIAL PRIMARY KEY, filename VARCHAR, s3_key VARCHAR, file_type VARCHAR);")
rds.commit()

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

    # Upload file to S3
    s3_key = f"uploads/{file.filename}"
    s3.upload_fileobj(file, S3_BUCKET, s3_key)

    # Save metadata to RDS
    with rds.cursor() as cursor:
        cursor.execute("INSERT INTO documents (filename, s3_key, file_type) VALUES (%s, %s, %s);", (file.filename, s3_key, file_type))
    rds.commit()

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
