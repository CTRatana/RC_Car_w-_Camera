import os
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from io import BytesIO

def authenticate_and_download_new_photos(folder_id, output_folder):
    credentials_path = 'uploadImageToGoogleDrive.json'
    scopes = ['https://www.googleapis.com/auth/drive.readonly']

    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=scopes
    )
    drive_service = build('drive', 'v3', credentials=credentials)

    while True:
        try:
            file_list = drive_service.files().list(q=f"'{folder_id}' in parents").execute().get('files', [])

            for file in file_list:
                file_id = file['id']
                file_name = file['name']

                if not os.path.exists(os.path.join(output_folder, file_name)):
                    request = drive_service.files().get_media(fileId=file_id)
                    fh = BytesIO()
                    downloader = MediaIoBaseDownload(fh, request)
                    done = False
                    while done is False:
                        status, done = downloader.next_chunk()
                        print(f"Download {int(status.progress() * 100)}%.")

                    with open(os.path.join(output_folder, file_name), 'wb') as f:
                        f.write(fh.getvalue())

                    print(f"Downloaded: {file_name} (ID: {file_id})")

            time.sleep(30)

        except Exception as e:
            print(f"An error occurred: {e}")
            time.sleep(10)

if __name__ == "__main__":
    folder_id = '1yMt9hQ5Q7L2ldjjQ59jxgGXZwS_EAUCc'
    output_folder = 'images'

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    authenticate_and_download_new_photos(folder_id,output_folder)
