import os
import time
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload, MediaIoBaseDownload
from io import BytesIO
from PIL import Image
import qrcode

FRAME_PATH = "frame.png"
CREDENTIALS_PATH = 'uploadImageToGoogleDrive.json'
UPLOAD_FOLDER_ID = "1bQyEb3IC5r8nI7V4iJDCIQsZIAjC4bym"
SLEEP_INTERVAL = 30

def get_drive_service(credentials_path):
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path,
        scopes=['https://www.googleapis.com/auth/drive.file']
    )
    return build('drive', 'v3', credentials=credentials)

def upload_image(service, file_path, destination_folder_id, file_name):
    media = MediaFileUpload(file_path, mimetype='image/png')

    try:
        file_metadata = {
            'name': file_name,
            'parents': [destination_folder_id]
        }
        uploaded_file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()

        file_id = uploaded_file.get('id')
        download_link = f"https://drive.google.com/uc?id={file_id}"

        print(f"File '{file_name}' uploaded to Google Drive folder with ID '{destination_folder_id}'")
        print(f"Download link: {download_link}")

        return download_link

    except Exception as e:
        print(f"An error occurred while uploading the file '{file_name}': {e}")
        return None

def add_qr_code_on_image(image_path, qr_code_path, output_directory, output_filename):
    image = Image.open(image_path).convert("RGBA")
    qr_code = Image.open(qr_code_path).convert("RGBA")

    qr_code = qr_code.resize((100, 100), Image.LANCZOS)

    position = (image.width - qr_code.width, image.height - qr_code.height)
    image.paste(qr_code, position, qr_code)

    output_path = os.path.join(output_directory, output_filename)
    image.save(output_path, "PNG")
    print(f"Image with QR code saved to {output_path}")

    return output_path

def add_frame(frame_path, raw_image_path, output_directory, output_filename):
    background = Image.open(frame_path).convert("RGBA")
    
    overlay = Image.open(raw_image_path).convert("RGBA")
    overlay = overlay.resize((700, 700), Image.LANCZOS)
    
    frame = Image.new("RGBA", background.size, (0, 0, 0, 0))
    
    position = ((background.size[0] - overlay.size[0]) // 2, (background.size[1] - overlay.size[1]) // 2)
    
    frame.paste(overlay, position, overlay)
    frame.paste(background, (0, 0), background)
    
    output_path = os.path.join(output_directory, output_filename)
    frame.save(output_path, "PNG")
    print(f"Overlay saved to {output_path}")
    
    return output_path

def generate_qr_code(download_link, output_directory, output_filename):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(download_link)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white")

    qr_code_path = os.path.join(output_directory, output_filename)
    qr_img.save(qr_code_path)
    print(f"QR code saved to {qr_code_path}")

    return qr_code_path

def download_raw_image(service, file_id, output_folder):
    request = service.files().get_media(fileId=file_id)
    fh = BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    done = False
    while not done:
        status, done = downloader.next_chunk()
        print(f"Download {int(status.progress() * 100)}%.")
    
    return fh.getvalue()

def download_raw_images(service, folder_id, output_folder):
    try:
        drive_service = get_drive_service(CREDENTIALS_PATH)
        file_list = drive_service.files().list(q=f"'{folder_id}' in parents").execute().get('files', [])

        for file in file_list:
            file_id = file['id']
            file_name = file['name']

            downloaded_image_path = os.path.join(output_folder, file_name)
            
            if not os.path.exists(downloaded_image_path):
                raw_image_data = download_raw_image(drive_service, file_id, output_folder)
                
                with open(downloaded_image_path, 'wb') as f:
                    f.write(raw_image_data)
                
                print(f"Downloaded: {file_name} (ID: {file_id}")

                frame_path = FRAME_PATH
                output_filename = f"{file_name}_with_frame.png"
                framed_image_path = add_frame(frame_path, downloaded_image_path, "addFrame", output_filename)

                download_link = upload_image(drive_service, framed_image_path, UPLOAD_FOLDER_ID, output_filename)

                qr_code_filename = f"{file_name}_qr_code.png"
                qr_code_filename_path = generate_qr_code(download_link, "QRCode", qr_code_filename)

                add_qr_code_on_image(framed_image_path, qr_code_filename_path, "FramedQRCode", qr_code_filename)

        time.sleep(SLEEP_INTERVAL)

    except Exception as e:
        print(f"An error occurred: {e}")
        time.sleep(SLEEP_INTERVAL)

def main():
    folder_id = '1yMt9hQ5Q7L2ldjjQ59jxgGXZwS_EAUCc'
    output_folder = 'images'

    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    while True:
        download_raw_images(CREDENTIALS_PATH, folder_id, output_folder)

if __name__ == "__main__":
    main()
