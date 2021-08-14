import json
from optparse import OptionParser
import requests

GET_TAG_URL = "https://quay.io/api/v1/repository/{org_name}/{repo_name}/tag?specificTag={tag_name}"
SECSCAN_URL = "https://quay.io/api/v1/repository/{org_name}/{repo_name}/manifest/{manifest_id}/security?vulnerabilities=true"


def generate_data(org_name, repo_name, tag_name, manifest, vulnerabilities):
    return {
        "Organisation": org_name,
        "Repository": repo_name,
        "Tag": tag_name,
        "Manifest": manifest,
        "Vulnerabilities": vulnerabilities
    }


if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option("-f", "--file", dest="filename")
    parser.add_option("-t", "--robot-token")
    (options, args) = parser.parse_args()
    result = []
    with open(options.filename) as f:
        repos = json.load(f)
        token = options.robot_token
        headers = {"Authorization": f"Bearer {token}",
                   "Content-type": "application/json"}
        for repo in repos:
            """
            1. For per tag get manifest
            2. For per manifet call sequence scan 
            """
            response = requests.get(headers=headers, url=GET_TAG_URL.format(org_name=repo['Organisation'],
                                                                            repo_name=repo['Repository'],
                                                                            tag_name=repo['Tag']))
            response.raise_for_status()
            data = response.json()
            tags = data['tags']
            if not tags:
                continue
            manifest_digest = tags[0]['manifest_digest']
            response = requests.get(headers=headers, url=SECSCAN_URL.format(org_name=repo['Organisation'],
                                                                            repo_name=repo['Repository'],
                                                                            manifest_id=manifest_digest))
            response.raise_for_status()
            data = response.json()
            features = data['data']['Layer']['Features']
            vulnerabilities = []
            for feature in features:
                if feature['Vulnerabilities']:
                    package_name = feature['Name']
                    vulnerabilities = feature['Vulnerabilities']
                    for vulnerability in vulnerabilities:
                        vulnerability['PackageName'] = package_name
            final_data = generate_data(org_name=repo['Organisation'],
                                       repo_name=repo['Repository'],
                                       tag_name=repo['Tag'],
                                       manifest=manifest_digest,
                                       vulnerabilities=vulnerabilities)
            result.append(final_data)
        print(json.dumps(result, indent=4, sort_keys=True))
