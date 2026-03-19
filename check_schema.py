import urllib.request
import json
url = "https://datasets-server.huggingface.co/info?dataset=ComplexDataLab/OpenFake"
response = urllib.request.urlopen(url)
data = json.loads(response.read().decode())
label_feature = data["dataset_info"]["train"]["features"]["label"]
print(f"Label Feature: {label_feature}")
