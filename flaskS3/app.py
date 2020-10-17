from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask import request
import boto3, os
from config import S3_BUCKET,S3_KEY,S3_SECRET

s3 = boto3.client(
    "s3",
    aws_access_key_id = S3_KEY,
    aws_secret_access_key = S3_SECRET
)
bucket_name = 'calacaschidas'
upload_folder = 'UpTest'

app_bbva = Flask(__name__)
Bootstrap(app_bbva)

@app_bbva.route('/')
def index():
    return render_template('index.html')

@app_bbva.route('/files', methods=['GET','POST'])
def files():
    s3_resource = boto3.resource('s3')
    my_bucket = s3_resource.Bucket(bucket_name)
    summaries = my_bucket.objects.all()
    return render_template('files.html', my_bucket=my_bucket, files = summaries)

@app_bbva.route('/upload',methods=['POST'])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        s3_resource = boto3.resource('s3')
        my_bucket = s3_resource.Bucket(bucket_name)

        #s3_resource.meta.client.upload_file('s3://calacaschidas/UpTest/'+file.filename, bucket_name, file.filename)
        #myobject = s3_resource.Object(bucket_name,'/UpTest/'+file.filename)

        #myobject.put() s3://calacaschidas/UpTest/08988068.pdf
        my_bucket.Object(file.filename).put(Body=file)

        
        #my_bucket.Object(file.filename).put(Body=open('/UpTest/', 'rb'))
        #s3_resource.meta.client.upload_file('/UpTest/' + file.filename, '<calacaschidas>', 'folder/{}'.format(file.filename))


        return render_template('files.html', my_bucket=my_bucket)

if __name__ == '__main__':
    app_bbva.run(debug=True)