"""
Script needs nine parameters to run:
1. Movie poster search URL
2. Movie poster URL
3. Database connection string
4. Database name
5. AWS S3 access key
6. AWS S3 secret key
7. AWS S3 bucket name
8. AWS S3 directory name
9. AWS S3 region
"""

from pymongo import MongoClient
from datetime import datetime
import boto3
from PIL import Image
from io import BytesIO
import urllib.request
import requests
import sys
import string

def upload_image(origin_url):
    access_key = sys.argv[5]
    secret_key = sys.argv[6]
    bucket_name = sys.argv[7]
    directory_name = sys.argv[8]
    region = sys.argv[9]

    s3 = boto3.client('s3', aws_access_key_id=access_key, aws_secret_access_key=secret_key, region_name=region)

    filename = origin_url.split('/')[-1]
    poster = urllib.request.urlopen(origin_url)
    img = Image.open(poster)

    in_memory_file = BytesIO(poster.read())
    img.save(in_memory_file, format=img.format)
    in_memory_file.seek(0)

    s3.upload_fileobj(in_memory_file, bucket_name, directory_name + '/' + filename, ExtraArgs={'ContentType': 'image/jpg'})
    s3_poster_url = 'https://{}.s3.{}.amazonaws.com/{}/{}'.format(bucket_name, region, directory_name, filename)

    return s3_poster_url

movieSearchUrl = sys.argv[1]
moviePosterUrl = sys.argv[2]
client = MongoClient(sys.argv[3])
db = client.get_database(sys.argv[4])

movies = db.movies.find({}, {'title':1, 'releaseDate':1, '_id':1})

for movie in movies:
    print('Updating \'{}\''.format(movie['title']))
    formattedMovieTitle = movie['title'].translate(movie['title'].maketrans('', '', string.punctuation))
    url = movieSearchUrl + formattedMovieTitle
    response = requests.get(url = url)
    data = response.json()
    if 'results' not in data:
        print('Could not find any results for \'{}\''.format(formattedMovieTitle))
        continue
    for result in data['results']:
        if 'release_date' not in result:
            print('No release date set for \'{}\' result'.format(formattedMovieTitle))
            continue
        releaseYear = result['release_date'].split('-')[0]
        movieReleaseYear = movie['releaseDate'].strftime("%Y")
        if releaseYear == movieReleaseYear and formattedMovieTitle in result['title']:
            posterPath = result['poster_path']
            if not posterPath:
                print('No poster available for this \'{}\' result'.format(formattedMovieTitle))
                continue

            posterUrl = moviePosterUrl + posterPath
            uploaded_image_url = upload_image(posterUrl)

            db.movies.update_one({'_id': movie['_id']}, {'$set': {'posterUrl': uploaded_image_url,
                                  'lastUpdated': datetime.strptime(datetime.today().isoformat() , '%Y-%m-%dT%H:%M:%S.%f')}})
            print('Updated \'{}\' with movie poster'.format(movie['title']))
            break