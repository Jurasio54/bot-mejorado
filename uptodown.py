from requests import get
from user_agent import generate_user_agent
import wget

def GetLink(url):
    if url.split('/')[-1] != 'descargar': url += '/descargar'
    r = get(url, headers={'user-agent': generate_user_agent()})
    return r.text.split('data-url=')[1].split('"')[1]
    
def Download(url, output=''):
    get_link = GetLink(url)
    file_name = output
    download = wget.download(get_link, file_name)
    return download