import requests
from omicspred.models import Dataset


def rest_api(folder_id:int, dev_token:str, offset:int=0) -> dict:
    rest_url = f'https://api.box.com/2.0/folders/{folder_id}/items?fields=name,shared_link'
    if offset:
        rest_url += f'&offset={offset}'
    print(f'- URL: {rest_url}')
    response = requests.get(rest_url, headers={"Content-Type" : "application/json", 'Authorization': f'Bearer {dev_token}'})
    response_json = response.json()
    if response_json:
        return response_json
    else:
        print(response)
        return None


def run(*args):
    # Update shared links (score.files_ids) using the Box REST API

    # Run example: python manage.py updated_shared_links --script-args 365934779636 metadata 123456 
    
    # Generate dev token: 
    # 1 - Go to https://app.box.com/developers/console
    # 2 - Click on App "OmicsPred - stats"
    # 3 - Click on "Configuration" tab
    # 4 - Click on the "Generate Developer Token" button
    # 5 - Copy token and add it as parameter to this script
    if args:
        folder_id = args[0]
        file_type = args[1]
        dev_token = args[2]

    if not folder_id or not file_type or not dev_token:
        print("- Missing parameter(s): folder_id, file_type or dev_token")
        exit(1)
    offset = 0
    limit = 100
    total_count = 0

    count_shared_links = 0
    count_total_files = 0
    # While loop because of pagination (limit 100)
    while offset < total_count or total_count == 0 :
        result = rest_api(folder_id, dev_token, offset)
        offset += limit
        total_count = result['total_count']
        count_total_files = total_count
        for entry in result['entries']:
            name = entry['name']
            # print(f"> Entry: {name}:\n{entry}")
            # File
            if entry['type'] == 'file':
                if 'shared_link' in entry.keys():
                    # print(entry['shared_link'])
                    url = entry['shared_link']['url']
                    dataset_id = name.split('_')[0]
                    file_id = url.replace('https://app.box.com/s/','')
                    print(f"- {dataset_id}: {file_id}")
                    count_shared_links += 1
                    if dataset_id:
                        try:
                            dataset = Dataset.objects.get(id=dataset_id)
                            files_ids = dataset.files_ids
                            if file_type not in files_ids.keys():
                                files_ids[file_type] = file_id
                                print(f"  > {files_ids}")
                                dataset.files_ids = files_ids
                                dataset.save()
                        except Dataset.DoesNotExist:
                            print(f"!!!!! Dataset {dataset_id} doesn't exist in the DB")
                else:
                    print(f"Shared link missing for {name}!")

    print(f"\n>> Shared links: {count_shared_links}/{count_total_files}")