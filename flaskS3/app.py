from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask import request
import boto3, botocore, os
from config import S3_BUCKET,S3_KEY,S3_SECRET
from filters import dateformat, gettype

s3 = boto3.client(
    "s3",
    aws_access_key_id = S3_KEY,
    aws_secret_access_key = S3_SECRET
)
#bucket_name = 'text0detection'
bucket_upload = 'calacaschidasdown'
bucket_download = 'calacaschidas'
upload_folder = 'UpTest'

app_bbva = Flask(__name__)
Bootstrap(app_bbva)
app_bbva.jinja_env.filters['dateformat'] = dateformat
app_bbva.jinja_env.filters['gettype'] = gettype

@app_bbva.route('/')
def index():
    return render_template('home.html')

@app_bbva.route('/files', methods=['GET','POST'])
def files():
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(bucket_upload)
    summaries = my_bucket.objects.all()
    return render_template('files.html', my_bucket=my_bucket, files = summaries)

@app_bbva.route('/upload',methods=['POST'])
def upload():
    if request.method == 'POST':
        s3_resource = boto3.resource('s3')
        my_bucket = s3_resource.Bucket(bucket_upload)
        for file in request.files.getlist("file[]"):
            print('name:'+str(file.filename)+'/ file:'+str(file))
            my_bucket.Object(file.filename).put(Body=file)

        return render_template('home.html', my_bucket=my_bucket)

@app_bbva.route('/tablas', methods=['GET','POST'])
def tablas():
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(bucket_upload)
    summaries = my_bucket.objects.all()
    return render_template('tablas.html',my_bucket=my_bucket, files = summaries)


if __name__ == '__main__':
    app_bbva.run(debug=True)