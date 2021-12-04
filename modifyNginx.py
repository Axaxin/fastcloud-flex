import subprocess as sp
import re
import os
import time

def loadConfig():
    print('正在读取设置文件....')
    try:
        with open('./user_info.txt') as f:
            rawdata = f.readlines()
    except:
        print('[Error]配置文件不存在...')
        return
    data = {}
    for line in rawdata:
        line = line.strip('\n')
        temp = line.split('=')
        if len(temp) < 2:
            data[temp[0]] = ''
        elif len(temp) == 2:
            data[temp[0]] = temp[1]
        elif len(temp) > 2:
            data[temp[0]] = '='.join(temp[1:])

    if verifyConfig(data):
        return data
    return


def verifyConfig(data):
    domain_pat = r'\w+\.\w+'
    email_pat = r'\w+@\w+\.\w'
    vhost_pat = r'\w+\.host'
    db_pat = r'\S'
    dbuser_pat = r'\S'
    dbpw_pat = r'\S'
    dbrootpw_pat = r'\S'
    upsize_pat = r'\d{1,4}[m|M|g|G]'

    pat_keys = data.keys()
    pat_vals = [domain_pat, email_pat, vhost_pat,
                db_pat, dbuser_pat, dbpw_pat, dbrootpw_pat, upsize_pat]
    pat_dict = dict(zip(pat_keys, pat_vals))

    statkeys = data.keys()
    statvals = []
    for k, v in data.items():
        if re.match(pat_dict[k], v):
            statvals.append(True)
        else:
            statvals.append(False)
    stat_dict = dict(zip(statkeys, statvals))
    invalid = []
    for k, v in stat_dict.items():
        if v == False:
            invalid.append(k)
    if len(invalid) > 0:
        print('配置项有误，请检查：')
        print(invalid)
        return False
    else:
        print('配置项看起来好像没什么问题...')
        return True


def attemptCheckSSl(domain,attempt=3,interval=15):
    files=os.listdir('./nginx/certs')
    pat=re.compile(domain+'\.[crt|cer|pem|key]')
    for i in range(attempt):
        print('正在检查ssl证书,尝试%d' % (i+1) )
        for item in files:
            if re.match(pat,item):
                return True
        time.sleep(interval)
    return

def modifyNginxConfig(domain, vhost, upload_size):
    print('正在配置Nginx...')
    while True:
        try:
            with open('./pkgs/nginx_sample.conf', 'r') as f:
                content = f.read()
        except:
            print('[Error]Nginx模版文件不存在')
            break
        pat1 = r'\$\{YOUR_DOMAIN\}'
        pat2 = r'\$\{VIRTUAL_HOST\}'
        pat3 = r'\$\{UPLOAD_SIZE\}'
        res = re.sub(pat1, domain,content)
        res = re.sub(pat2, vhost,res)
        res = re.sub(pat3, upload_size,res)
        try:
            with open('./nginx/conf/proxy.conf', 'w+') as f:
                f.write(res)
        except:
            print('[Error]Nginx配置出错...')
            break
        print('Nginx配置已经添加...')
        return True
    return


def reloadNginx():
    stmt = 'docker exec nginx-proxy nginx -s reload'
    ret, out = sp.getstatusoutput(stmt)
    pat = r'[0-9a-zA-Z\s\[\]\:\#\s\/]*signal\sprocess\sstarted'
    checkOutput = re.match(pat, out)
    if ret == 0 and checkOutput:
        print('Nginx已经重载...')
        return True
    else:
        print('Nginx重载失败...')
        return False
    

if __name__ == "__main__":
    # 载入用户预设
    configs=loadConfig()

    while True:
        # 检查acme是否生成证书
        res=attemptCheckSSl(configs['YOUR_DOMAIN'])
        if not res:
            break
        # 修改配置
        res = modifyNginxConfig(
            configs['YOUR_DOMAIN'], configs['VIRTUAL_HOST'], configs['UPLOAD_SIZE'])
        if not res:
            break

        # 重载Nginx
        res = reloadNginx()
        if not res:
            break
        print('部署成功!')
        print('退出')
        exit()

    print('配置失败。。。')
