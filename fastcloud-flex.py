import subprocess as sp
import re
import time


def getDNS(domain):
    stmt = 'ping ' + domain+' -c 1'
    pattern_1 = re.compile(domain+'\s\(\d+.\d+.\d+.\d+\)')
    pattern_2 = r'\d+.\d+.\d+.\d'
    out, err = sp.getstatusoutput(stmt)
    if out == 0:
        filterRes = re.findall(pattern_1, err)
        res = re.findall(pattern_2, filterRes[0])
        return res[0]
    else:
        return 'None'


def getIP():
    stmt = 'curl https://api-ipv4.ip.sb/ip'
    out, err = sp.getstatusoutput(stmt)
    pat = r'\d+.\d+.\d+.\d'
    if out == 0:
        res = re.findall(pat, err)
        return res[0]
    else:
        return 'none'


def checkDNS(domain):
    print('正在检测DNS...')
    dns = getDNS(domain)
    ip = getIP()
    print('-'*30)
    print('你输入的域名为：'+domain)
    print("DNS解析为："+dns)
    print('你的IP是：'+ip)
    print('-'*30)
    time.sleep(2)
    if dns == ip:
        print('DNS解析和本地ip相符，可以继续')
        return True
    else:
        print('域名解析与本地ip不相符，请检查DNS再试。')
        return False


def checkDocker():
    print('正在检测Docker...')
    stmt = 'docker -v'
    retcode, output = sp.getstatusoutput(stmt)
    if retcode == 0:
        docker_version = re.split(r'[\s\,]+', output)[-1]
        print('Docker已经存在，版本为：'+docker_version)
        return docker_version
    else:
        print('未检测到docker版本...')
        return 'None'


def checkDodckerCompose():
    print('正在检测docker-compose...')
    stmt = 'docker-compose -v'
    retcode, output = sp.getstatusoutput(stmt)
    if retcode == 0:
        dcompose_version = re.split(r'[\s\,]+', output)[-1]
        print('Docker-compose已经存在，版本为：'+dcompose_version)
        return dcompose_version
    else:
        print('未检测到docker-compose版本...')
        return 'None'


def installDocker():
    print('正在准备安装Docker...')
    downloadDockerScrpit = 'curl -fsSL https://get.docker.com -o get-docker.sh'
    execDockerScript = 'sh get-docker.sh'
    retcode, output = sp.getstatusoutput(downloadDockerScrpit)
    if retcode == 0:
        try:
            sp.run(execDockerScript, shell=True, check=True)
            print('Docker 安装成功！')
            return True
        except:
            print('Docker 安装失败，请检查你的网络连接.')
            return False
    print('执行docker自动安装脚本失败...')
    return False


def installDockerCompose():
    print('正在准备安装docker-compose...')
    installDockerCompsoe = 'apt-get install docker-compose'
    try:
        sp.run(installDockerCompsoe, shell=True,
               input='y', encoding='utf-8', check=True)
        print('Docker-compose 安装完成！')
        return True
    except:
        print('Docker-compose 安装失败，请检查你的网络连接.')
        return False


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


def modifyEnvFile(data):
    print('正在设置docker-compose变量...')
    line1 = 'YOUR_DOMAIN='+data['YOUR_DOMAIN']
    line2 = '\nVIRTUAL_HOST='+data['VIRTUAL_HOST']
    line3 = '\nYOUR_MYSQL_DATABASE='+data['YOUR_MYSQL_DATABASE']
    line4 = '\nYOUR_MYSQL_USER='+data['YOUR_MYSQL_USER']
    line5 = '\nYOUR_MYSQL_PASSWORD='+data['YOUR_MYSQL_PASSWORD']
    line6 = '\nYOUR_MYSQL_ROOT_PASSWORD='+data['YOUR_MYSQL_ROOT_PASSWORD']

    content = line1+line2+line3+line4+line5+line6
    try:
        with open('./.env.fastcloud', 'w+') as f:
            f.write(content)
    except:
        print('[Error]配置文件路径有误...')
        return False
    print('docker-compose环境变量配置成功...')
    return True


def modifyACMEFile(domain):
    print('正在配置acme-profile....')
    whatever = 15165
    uniqueid = 'app'+str(whatever)
    line1 = "LETSENCRYPT_STANDALONE_CERTS=('"+uniqueid+"')"
    line2 = "\nLETSENCRYPT_"+uniqueid+"_HOST=('"+domain+"')"
    content = line1+line2
    with open('./pkgs/acme_profile.sh', 'w+') as f:
        f.write(content)
    pass


def modifyNginxConfig(domain, vhost, upload_size):
    print('正在配置Nginx...')
    while True:
        try:
            with open('./pkgs/nginx_sample.conf', 'r') as f:
                content = f.read()
        except:
            print('[Error]Nginx模版文件不存在')
            break
        pat1 = r'${YOUR_DOMAIN}'
        pat2 = r'${VIRTUAL_HOST}'
        pat3 = r'${UPLOAD_SIZE}'
        res = re.sub(pat1, content, domain)
        res = re.sub(pat2, res, vhost)
        res = re.sub(pat3, res, upload_size)
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
    stmt = 'docker exec nginx nginx -s reload'
    ret, out = sp.getstatusoutput(stmt)
    pat = r'[0-9a-zA-Z\s\[\]\:\#\s\/]*signal\sprocess\sstarted'
    checkOutput = re.match(pat, out)
    if ret == 0 and checkOutput:
        print('Nginx已经重载...')
        return True
    else:
        print('Nginx重载失败...')
        return False


def deployImages():
    print('正在部署fastcloud套件...')
    dcomposeUp = 'docker-compose --env-file .env.fastcloud up -d'
    try:
        sp.run(dcomposeUp, shell=True, check=True)
    except sp.CalledProcessError as e:
        print(e)
        print('fastcloud套件部署失败...')
        return False
    print('fastcloud套件部署成功！')
    return True


if __name__ == "__main__":
    print('')
    print('')
    print('         fastcloud-flex')
    print('   ---authored by Axaxxin---')
    print('   https://github.com/Axaxxin')
    print('')

    toInstall = False
    # 检查信息预设再启动主要的安装
    configs = loadConfig()
    if configs:
        # 先检查DNS再执行安装步骤
        res = checkDNS(configs['YOUR_DOMAIN'])
        if res:
            toInstall = True

    while toInstall == True:
        # 检查和安装Docker相关
        res = checkDocker()
        if res == 'None':
            res = installDocker()
            if res != True:
                break
        
        res = checkDodckerCompose()
        if res == 'None':
            res = installDockerCompose()
            if res != True:
                break
        
        # 设置配置并开始部署容器
        res = modifyACMEFile(configs['YOUR_DOMAIN'])
        if res != True:
            break
        res = modifyEnvFile(configs)
        if res != True:
            break
        res = deployImages()
        if res != True:
            break
        
        # 给时间让容器启动和生效
        print('等待acme生成ssl证书...')
        waittime = 16
        for i in range(waittime)[-1::-1]:
            print('等待剩余 '+str(i)+'秒...', end='\r')
            time.sleep(1)

        # 修改配置
        res = modifyNginxConfig(
            configs['YOURDOMAIN'], configs['VIRTUAL_HOST'], configs['UPLOAD_SIZE'])
        if res != True:
            break

        # 重载Nginx
        res = reloadNginx()
        if res != True:
            break
        print('部署成功!')
        print('退出')
        exit()
    print('部署失败！')
