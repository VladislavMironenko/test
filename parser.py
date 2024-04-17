from dateutil.parser import parse
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
import json
import requests
import os
import schedule
import time
import sched





def start_schedule():
    IMAGE_FOLDER = "Images"

    def download_image(image_url, title, filename, folder_path):
        try:
            response = requests.get(image_url)
            if response.status_code == 200:
                image_data = response.content
                if not os.path.exists(folder_path):
                    os.makedirs(folder_path)
                file_path = os.path.join(folder_path, filename)
                with open(file_path, "wb") as f:
                    f.write(image_data)
                    print(f"Image saved: {file_path}")
        except:
            print(f"Error downloading image: {image_url}")

    def extract_data(url):
        data_list = []
        response = requests.get(url)
        data = response.json()
        if isinstance(data, dict):
            data_list.append(data)
        elif isinstance(data, list):
            data_list.extend(data)
        result = []
        try:
            for item in data_list[0:2]:
                item_dict = {
                    'id': item.get('id', ''),
                    'link': item.get('link', ''),
                    'title': item.get('title', '').get('rendered', '') if 'title' in item else item.get('name', ''),
                    'date': item.get('date', ''),
                    'status': item.get('status', '')
                }

                date = None
                try:
                    soup2 = BeautifulSoup(requests.get(item_dict['link']).text, 'html.parser')
                    pages = soup2.find(class_='navi_center')
                    try:
                        pages = int(pages.find_all('a')[-2].text.strip())
                    except:
                        pages = 1
                    for page in range(1, pages + 1):
                        soup = BeautifulSoup(requests.get(f"{item_dict['link']}page/{page}").text, 'html.parser')
                        all_links = soup.find_all(class_='postTitle_archive')
                        for link in all_links:
                            response = requests.get(link.find('a').get('href', ''))
                            soup2 = BeautifulSoup(response.text, 'html.parser')
                            date = soup2.find(class_='date_time').find(class_='post-time').text.strip()
                            try:
                                date = parse(date, fuzzy=True)
                            except ValueError:
                                pass
                except:
                    soup2 = BeautifulSoup(requests.get(item_dict['link']).text, 'html.parser')
                    date = None

                content_soup = soup2.find(class_='postContent').find_all('p')
                folder_path = os.path.join(IMAGE_FOLDER, item_dict['title'])
                for content_item in content_soup:
                    try:
                        image_url = content_item.find('img').get('data-src')
                        download_image(image_url, item_dict['title'], f"{hash(content_item)}.jpg", folder_path)
                    except:
                        continue

                users = soup2.find(class_='date_time').find(class_='post_view').text.strip()
                description = soup2.find(class_='postContent').find_all('p')[0].text.strip()
                image_path = os.path.join(folder_path, f"{hash(content_item)}.jpg")

                result_item = {
                    'id': item_dict['id'],
                    'title': item_dict['title'],
                    'description': description,
                    'link': item_dict['link'],
                    'users': users,
                    'date': str(date),
                    'Image': str(os.path.relpath(image_path, start=os.path.dirname(__file__))),
                    'status': item_dict['status']
                }
                result.append(result_item)
        except Exception as e:
            print(e)
        return result


    def main():
        link_list = ['https://www.9minecraft.net/wp-json/wp/v2/tags?page=3',
                     'https://www.9minecraft.net/wp-json/wp/v2/posts?page=3&tags=14576&per_page=15',
                     'https://www.9minecraft.net/wp-json/wp/v2/posts/664098']
        data = []
        for link in link_list:
            data.extend(extract_data(link))
        with open('data.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    while True:
        main()
        next_run = datetime.now() + timedelta(days=5)
        timestamp = time.mktime(next_run.timetuple())
        time.sleep(timestamp - time.time())


if __name__ == '__main__':
    start_schedule()