#Metadata file is extracted in the

import json, requests, csv, sys, os,re
import xml.etree.ElementTree as ET

read_file="application_list.csv"
#read_file="test_applications.csv"
failed_apps="failed_apps.csv"
get_app_file="get_app_list.csv"
api_key="<api_key>"
okta_tenant="https://<tenant>.okta.com"

payload = {}
headers = {
  'Accept': 'application/json',
  'Content-Type': 'application/json',
  'Authorization': 'SSWS '+api_key
}


failed_deactivations=[]
get_app_list=[]

# Read applications list, build in memory list of applications
with open(read_file, 'r') as application_list:
    groups = csv.reader(application_list)
    #Assuming AppID header
    next(application_list)

    for app in application_list:

        #Using the App ID, get application attributes
        application=re.sub(r"\W",'',app)
        get_app_url = okta_tenant+"/api/v1/apps/"+application
        get_app_response = requests.request("GET", get_app_url, headers=headers, data = payload)
        get_app_list.append(get_app_response.json())
        print(app)
        print(get_app_url)

# extract metadata from each app
with open(get_app_file, 'w', newline='') as get_apps_file:
    header=["appid","label","name","ssoMode","publicMetadataURI","idpSsoUrl","idpIssuer"]
    csv_writer=csv.DictWriter(get_apps_file, fieldnames=header)
    csv_writer.writeheader()
    #write each app in get_app_list
    for app in get_app_list:
        # Extract app ID
        appid=app['id']

        # Extract app label (Display name)
        label=app['label']

        # Extract app name
        name=app['name']

        print(appid+" - "+label+" - "+name)

        # Extract ssoMode
        ssoMode=app['signOnMode']
        print(ssoMode)
        if ssoMode=="SAML_2_0":

            # Get metadata file
            metadata=app['_links']['metadata']['href']
            metadata_headers = {
              'Accept': 'application/xml',
              'Content-Type': 'application/json',
              'Authorization': 'SSWS '+api_key
            }
            metadata_file=ET.fromstring(requests.request("GET", metadata, headers=metadata_headers, data = payload).text.encode("utf8"))

            # Extract entityID
            idpIssuer=metadata_file.attrib['entityID']

            # Extract SSO URL
            print(len(metadata_file[0]))
            if len(metadata_file[0]) >4:
                idpSsoUrl=metadata_file[0][4].attrib['Location']
            else:
                idpSsoUrl=metadata_file[0][3].attrib['Location']

            # Extract public metadata file
            metadata = okta_tenant + "/app/"+idpIssuer.split("http://www.okta.com/")[1]+"/sso/saml/metadata"
            print(metadata)

        else:
            metadata=""
            idpIssuer=""
            idpSsoUrl=""

        app_profile={'appid':appid,"label":label,"name":name,"ssoMode":ssoMode,"publicMetadataURI":metadata,"idpSsoUrl":idpSsoUrl,"idpIssuer":idpIssuer}
        csv_writer.writerow(app_profile)
