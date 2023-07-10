## LAVA + KernelCI环境搭建和使用

#### 1. 环境准备

###### 1.1.1 硬件环境

一台ubuntu 22.04 x86电脑: 部署LAVA和KernelCI(也可以用二台ubuntu 22.04 x86电脑分别部署LAVA和KernelCI)

一台sifive-unmatched: 执行测试的设备，通过USB串口连接到x86电脑，并插入已经烧录u-boot镜像的T-Flash卡，且确保从T-Flash卡启动

一台starfive-visionfive: 执行测试的设备，通过USB串口连接到x86电脑，并插入已经烧录u-boot镜像的T-Flash卡

一台继电器: 通过杜邦线与sifive-unmatched和starfive-visionfive相连，用于控制这两台设备的电源

这四台设备在同一个局域网中

###### 1.2 软件环境

在部署主机上需要安装一些软件包和启动一些服务

###### 1.2.1 在部署机器上安装qemu作为slave执行boards

````
$ sudo apt install qemu-system-misc
````

###### 1.2.2 安装NFS server

````
$ sudo apt install nfs-kernel-server
$ vim /etc/exports    //配置NFS共享目录
/var/lib/lava/dispatcher/tmp *(rw,no_root_squash,no_all_squash,async,no_subtree_check)
$ sudo service nfs-kernel-server restart   //配置完成后重启NFS server
````

###### 1.2.3 安装ser2net

安装ser2net为了部署主机通过telnet可以连接到测试设备

````
$ sudo apt install ser2net
$ sudo vim /etc/ser2net.yaml     //配置串口信息
connection: &con0096
    accepter: tcp,20000
    enable: on
    options:
      banner: *banner
      kickolduser: true
      telnet-brk-on-sync: true
    connector: serialdev,
              /dev/ttyUSB1,
              115200n81,local

connection: &con1096
    accepter: tcp,20001
    enable: on
    options:
      banner: *banner
      kickolduser: true
      telnet-brk-on-sync: true
    connector: serialdev,
              /dev/ttyUSB2,
              115200n81,local
$ sudo service ser2net restart     //重启ser2net service
````

###### 1.2.4 安装mqtt server

由于需要通过mqtt来控制设备的电源，所以需要安装mqtt sever, 这里使用的是mosquitto，安装方法可以参考 https://www.vultr.com/docs/install-mosquitto-mqtt-broker-on-ubuntu-20-04-server/

安装mosquitto

````
$ sudo apt update
$ sudo apt install -y mosquitto
$ sudo systemctl status mosquitto
$ sudo systemctl enable mosquitto      //设置为开机自动启动mosquitto service
````

配置mosquitto, 创建配置文件

````
$ sudo vim /etc/mosquitto/conf.d/default.conf
````

配置文件内容

````
listener 1883
allow_anonymous false      //不允许匿名用户连接
password_file /etc/mosquitto/passwd        //指定password_file路径
````

创建/etc/mosquitto/passwd文件

````
$ sudo vim /etc/mosquitto/passwd
````

编辑用户名密码

````
<username>:<password>      //用户名:密码
````

使用mosquitto_passwd将密码文件/etc/mosquitto/passwd加密

````
$ sudo mosquitto_passwd -U /etc/mosquitto/passwd
````

查看是否加密成功

````
$ sudo cat /etc/mosquitto/passwd
````

配置完成后重启mosquitto service

````
$ sudo systemctl restart mosquitto
````

###### 1.2.5 安装docker环境

由于使用docker compose部署LAVA和Kernel CI，所以需要安装docker和docker compose, 安装方法参看 https://docs.docker.com/engine/install/ubuntu/  

为了方便不用sudo执行docker命令，可以将当前用户添加到docker组内

```
$ sudo groupadd docker    //添加docker用户组
$ sudo usermod -a -G docker $(whoami)    //将当前用户添加到docker组内
$ sudo systemctl restart docker     //重启docker service
````
执行完以上命令，退出当前终端操作界面再次进入，就可以不用sudo执行docker命令了

###### 1.2.6 安装python虚拟环境

为了部署kernelci环境干净，最好安装python虚拟环境，在python虚拟环境中部署kernelci

python虚拟环境安装可以参看 https://blog.csdn.net/qq_52385631/article/details/123590584

#### 2. Kernel CI环境搭建

##### 2.1 获取源码

用docker compose部署kernel ci前后端和数据库，由于官方提供的kernelci-docker( https://github.com/kernelci/kernelci-docker )中的kernelci-frontend和kernel-backend关联的代码版本比较旧，我做了更新，和kernel ci官网前后端代码版本保持一致（ https://linux.kernelci.org ），更新后的kernelci-docker源码存储在 https://github.com/jiewu-plct/kernelci-docker

````
$ git clone https://github.com/jiewu-plct/kernelci-docker.git
$ cd kernelci-docker
$ git submodule init
$ git submodule update
````

##### 2.2 修改源码

###### 2.2.1 dev-start.sh文件

dev-start.sh是用来部署kernelci的脚本，修改的内容包括：

A) 将脚本中旧版的docker-compose命令修改为docker compose，否则部署时会报错

B）根据需要可以修改脚本中外部访问前端，后端，nginx自带file server的port(可选)

###### 2.2.2 dev-stop.sh文件

dev-stop.sh是用来停止kernelci运行的脚本，修改内容就是将脚本中旧版的docker-compose命令修改为docker compose，否则部署时会报错

###### 2.2.3 docker-compose.yml文件

docker-compose.yml是用来创建并运行kernelci相关的所有docker容器的部署文件，如果dev-start.sh文件中修改了B), 那么该文件中对应的port也要做相应的修改

###### 2.2.4 backend/Dockerfile-celery

Dockerfile-celery是用来创建celery docker image的文件，修改的内容是将其中安装包的命令install_packages改为apt update && apt install -y，否则会导致安装包不成功

###### 2.2.5 frontend/kernelci-frontend/app/dashboard/static/js/app/utils/urls.js

修改创建查看lava job log的存储路径，新增data.build_environment，否则创建的路径会与实际存储到nginx自带的file server路径不符，导致前端无法查看

````
translatedURL = [null, null];
        if (serverURL) {
            serverURI = new URI(serverURL);

            translatedURL[0] = serverURI;

            if (data.file_server_resource) {
                translatedURL[1] = URI
                    .joinPaths(serverURI.path(), data.file_server_resource)
                    .path();
            } else {
                if (data.version === '1.0') {
                    translatedURL[1] = URI
                        .joinPaths(
                            data.job,
                            data.kernel,
                            data.arch + '-' +
                            (data.defconfig_full || data.defconfig),
			    data.build_environment)      //新增data.build_environment
                        .path();
                } else {
                    translatedURL[1] = URI
                        .joinPaths(
                            data.job,
                            data.git_branch,
                            data.kernel,
                            data.arch,
                            (data.defconfig_full || data.defconfig),
			    data.build_environment)     //新增data.build_environment
                        .path();
                }
            }
        }
````

##### 2.3 部署KernelCI

````
$ ./dev-start.sh
````

部署完成后，会在源码根目录下生成文件.kernelci_token，该文件中存储了可以访问kernelci后端的账号admin对应的token

如果要停止运行kernelci, 执行

````
$ ./dev-stop.sh
````

部署完成后，在浏览器中输入http://192.168.1.100:8080可以进入kernel ci的web界面

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/kernelci-1.JPG)

##### 2.4 创建lab

部署完成后，需要通过访问kernelci api来创建lab, 否则无法和lava进行交互。这里写了一个python脚本来实现这个功能

````
import json
import requests

BACKEND_URL = "http://192.168.1.100:8081"
AUTHORIZATION_TOKEN = "47db837b-8e2c-45b0-846f-44345a076f7f"

def create_lab():
    headers = {
        "Authorization": AUTHORIZATION_TOKEN,
        "Content-Type": "application/json"
    }

    payload = {
        "name": "lab-01",
        "contact": {
            "name": "aaaa",
            "surname": "bbbb",
            "email": "aaaa@cccc.com"
        }
    }

    url = BACKEND_URL + '/lab'
    response = requests.post(url, data=json.dumps(payload), headers=headers)
    print (response.content)

if __name__ == "__main__":
    create_lab()
````

其中：

BACKEND_URL：部署kernelci主机的ip以及访问kernelci后端的端口

AUTHORIZATION_TOKEN：.kernelci_token文件中存储的token

payload：根据需要填写lab名称和lab联系人的名字和email

这个脚本 create-lab.py 已存储在本仓库中，执行以下命令运行该脚本

````
$ pip install requests  //安装需要用到的python第三方库
$ python create-lab.py   //运行脚本
b'{"result":[{"name":"lab-01","_id":{"$oid":"646f330d2c6e1b3674e32aec"},"token":"ff5ebf29-338b-469f-8f48-32aff3acbba1"}],"code":201}'
````

其中 "token":"ff5ebf29-338b-469f-8f48-32aff3acbba1" 就是后面和lava进行交互需要用到的token

#### 3. LAVA环境搭建

##### 3.1 获取lava源码

用docker compose部署LAVA, 从 https://github.com/kernelci/lava-docker 获取源码

````
$ git clone https://github.com/kernelci/lava-docker.git
$ cd lava-docker
````

##### 3.2 准备设备类型模板

目前配合LAVA使用的设备有qemu, unmatched, visionfive, 每一类设备都需要有对应的设备类型模板

qemu：设备类型模板在源码中已有

unmatched：设备类型模板在源码中没有适合的，需要另外编写和添加

编写方式可以参考 https://validation.linaro.org/static/docs/v2/device-integration.html?highlight=device%20types

添加方式是将需要新增的设备类型模板存放到lava-docker/lava-master/device-types/目录下

visionfive：设备类型模板虽然在源码中有相关的，但需要修改，目前采取的方式是将修改好的模板在部署时用映射的方式来取代源码中的模板

unmatched和visionfive设备类型模板已存储在本仓库中的device-types-template目录下，供参考。

##### 3.3 修改lava源码

###### 3.3.1 lavalab-gen.py文件

源码获取后可以根据需要，编辑lavalab-gen.py文件, 修改生成docker-compose.yml文件中的master和slave的参数：

master参数

````
dockcomp = {}
dockcomp["version"] = "2.0"
dockcomp["services"] = {}
dockcomposeymlpath = "output/%s/docker-compose.yml" % host
dockcomp["services"][name] = {}
dockcomp["services"][name]["hostname"] = name
dockcomp["services"][name]["ports"] = [ str(webinterface_port) + ":80", "5555:5555", "5556:5556", "5500:5500" ]
dockcomp["services"][name]["volumes"] = [ "/boot:/boot", "/lib/modules:/lib/modules", "/home/plct/Documents/kernelci_inlinepath/jh7100-visionfive.jinja2:/usr/share/lava-server/device-types/jh7100-visionfive.jinja2" ]          //用修改后的visionfive设备类型模板替换源码中的模板
dockcomp["services"][name]["build"] = {}
dockcomp["services"][name]["build"]["context"] = name
dockcomp["services"][name]["restart"] = "always"      //添加开机自动运行参数
````

slave参数

````
dockcomp["services"][name] = {}
dockcomp["services"][name]["hostname"] = name
#dockcomp["services"][name]["dns_search"] = ""       //注释词条语句，否则无法部署成功
dockcomp["services"][name]["ports"] = []
dockcomp["services"][name]["volumes"] = [ "/boot:/boot", "/lib/modules:/lib/modules", "/home/plct/Documents/kernelci_inlinepath:/home/inlinepath", "/home/plct/Documents/kernelci_inlinepath/acme-cli:/usr/local/bin/acme-cli" ]          //添加需要挂载的目录，并将远程控制电源的脚本映射到slave容器中
dockcomp["services"][name]["environment"] = {}
dockcomp["services"][name]["build"] = {}
dockcomp["services"][name]["build"]["context"] = name
dockcomp["services"][name]["restart"] = "always"       //添加开机自动运行参数
dockcomp["services"][name]["privileged"] = True        //添加privileged参数
````

###### 3.3.2 boards.yaml文件

编辑boards.yaml

每一项参数的意义可以参看 https://github.com/kernelci/lava-docker

````
---
masters:
  - name: master
    host: local
    webinterface_port: 8000      //设置web访问端口
    allowed_hosts: ['*']         //设置任意设备都可以访问web界面，否则只能在部署的主机上访问
    users:      //设置登录lava的账号及账号权限
      - name: admin
        token: adminlavatoken
        password: adminpassword
        superuser: true                  
        staff: true
    tokens:    //设置访问kernelci后端的token
    - username: admin
      token: ff5ebf29-338b-469f-8f48-32aff3acbba1
      description: kernelci-token
slaves:
  - name: lab-slave-1
    host: local
    remote_master: master
    remote_user: admin
    dispatcher_ip: 192.168.1.100        //部署主机IP
    use_tftp: True
    use_nfs: True
    host_healthcheck: false

boards:
  - name: qemu-test
    type: qemu
    slave: lab-slave-1
  - name: sifive-unmatched_01
    type: sifive-unmatched
    slave: lab-slave-1
    connection_command: telnet 192.168.1.100 20000    //20000是1.2.3中ser2net配置的串口/dev/ttyUSB1对应的端口
    pdu_generic:    //远程控制unmatched电源的命令
      hard_reset_command: /usr/local/bin/acme-cli -s 192.168.1.100 -d unmatched reset 4
      power_off_command: /usr/local/bin/acme-cli -s 192.168.1.100 -d unmatched switch_off 4
      power_on_command: /usr/local/bin/acme-cli -s 192.168.1.100 -d unmatched switch_on 4
    uart:   
      idvendor: 0x0403
      idproduct: 0x6010
      devpath: "1"
  - name: starfive-visionfive_01
    type: jh7100-visionfive
    slave: lab-slave-1
    connection_command: telnet 192.168.1.100 20001   //20001是1.2.3中ser2net配置的串口/dev/ttyUSB2对应的端口
    pdu_generic:    ////远程控制visionfive电源的命令
      hard_reset_command: /usr/local/bin/acme-cli -s 192.168.1.100 -d visionfive reset 2
      power_off_command: /usr/local/bin/acme-cli -s 192.168.1.100 -d visionfive switch_off 2
      power_on_command: /usr/local/bin/acme-cli -s 192.168.1.100 -d visionfive switch_on 2
    uart:
      idvendor: 0x067b
      idproduct: 0x2303
      devpath: "3"
````

远程控制设备电源使用的是继电器+mqtt的方式实现的，并用python编写了server和client脚本：

acme-service.py: server脚本在部署主机上运行

acme-cli: client脚本映射到slave容器中，通过执行相应的命令来运行

````
$ /usr/local/bin/acme-cli -s 192.168.1.100 -d visionfive reset 2
````

其中192.168.1.100对应的是运行acme-service.py的主机IP，2对应的是设备连接在继电器上的端口号

为了方便，可以将acme-service.py配置成service来进行管理，配置的方法是在/etc/systemd/system/目录下创建一个server文件，例如创建acme.service文件，内容如下：

````
[Unit]
Description=run acme server script
After=multi-user.target

[Service]
Type=idle
ExecStart=python3 /home/plct/Documents/mosquitto/acme-service.py    //运行acme-service.py的命令

[Install]
WantedBy=multi-user.target
````

配置完成后就可以通过systemctl管理acme-service.py

````
$ sudo systemctl daemon-reload      //使配置文件生效
$ sudo systemctl enable acme       //设置为开机自动运行
$ sudo systemctl start acme        //运行acme-service.py脚本
$ sudo systemctl stop acme         //停止运行acme-service.py脚本
````

另外需要注意的是，运行acme-service.py，需要安装脚本用到的python第三方库

````
$ sudo pip install paho-mqtt
````

##### 3.4 部署lava

````
$ ./lavalab-gen.py   //生成部署需要的文件, 存放在output/local/目录下
$ cd output/local
$ docker compose build //生成lava master和slave的docker image
$ docker compose up -d    //运行lava master和slave docker容器
````

#### 4. LAVA的使用

##### 4.1 手动运行lava job

在浏览器中输入http://192.168.1.100:8000 进入lava web界面，其中192.168.1.100是部署lava的主机的IP，8000是boards.yaml中设置的webinterface_port

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/lava-1.JPG)

登录的用户名和密码是boards.yaml中设置的users的name和password, 登录后点击Scheduler->Device Types，显示当前可以使用的设备类型

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/lava-2.JPG)

点击Scheduler->Device Types，显示当前可以使用的设备信息

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/lava-3.JPG)

所使用设备只有Health是Good或者Unknown时才可执行job, Health状态可以手动修改，修改方式是在该界面点击所要修改的Hostname->点击Health栏位后面的编辑图标->进入Device health对话框界面，修改Health->Set health保存

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/lava-4.JPG)

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/lava-5.JPG)

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/lava-6.JPG)

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/lava-7.JPG)

这里需要注意的是qemu设备类型会定期自动执行Health Check，刚部署完就会执行

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/lava-8.JPG)

点击Scheduler->Submit->进入Submit Job界面，在该界面添加要执行的job->点击Submit->进入job执行界面

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/lava-9.JPG)

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/lava-10.JPG)

点击Scheduler->Jobs可以看到系统中所有job的状态和信息

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/lava-11.JPG)

关于job的语法，可以参看 https://validation.linaro.org/static/docs/v2/first-job.html#index-1

关于job中actions部分的详细说明，可以参看

deploy: https://validation.linaro.org/static/docs/v2/actions-deploy.html#index-38

boot: https://validation.linaro.org/static/docs/v2/actions-boot.html#index-0

test: https://validation.linaro.org/static/docs/v2/actions-test.html#index-0

##### 4.2 lava与kernelci交互

如果要将lava job执行结果传到kernelci，需要在job中添加metadata和notify的相关信息

````
metadata:
  job.arch: riscv64
  job.build_environment: gcc-11.3.0
  kernel.defconfig: defconfig
  kernel.defconfig_full: defconfig
  device.type: sifive-unmatched
  platform.dtb: hifive-unmatched-a00.dtb
  kernel.endian: little
  git.branch: master
  git.commit: 44c026a73be8038f03dbdeef028b642880cf1511
  git.describe: v6.4-rc3
  git.url: https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git
  job.initrd_url: none
  kernel.tree: mainline
  kernel.version: v6.4-rc3
  job.kernel_image: image
  test.plan: ltp
  test.plan_variant: ltp-syscalls
  platform.mach: riscv
notify:
  criteria:
    status: finished
  callbacks:
    - url: http://192.168.1.100:8081/callback/lava/test?lab_name=lab-01&status={STATUS}&status_string={STATUS_STRING}
      method: POST
      dataset: all
      token: kernelci-token
      content-type: json
````

上面列出的metadata和notify每一项都是必填项，否则无法成功存储到kernelci的数据库中

关于notify的详细说明，可以参看 https://validation.linaro.org/static/docs/v2/user-notifications.html?highlight=callback

其中：

url中的192.168.1.100:8081是访问kernelci后端的地址和端口

lab_name=lab-01是上述2.4中创建的lab名称

token是3.3.2中boards.yaml里设置的tokens字段里的description

lava job执行完成后，进入kernelci界面的Tests界面和SoCs界面可以看到测试结果以及lava job执行的log

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/kernelci-2.JPG)

![image](https://github.com/jiewu-plct/kernel-ci/blob/main/kernelci-image/kernelci-3.JPG)

可以成功执行得lab job的例子存放在本仓库中的lava-job-example目录下，供参考。

##### 4.3 自动触发lava job

可以用github actions来触发submit lava job。另外由于执行lava job之前需要先将kernel image构建好，所以可以将构建kernel image的submit lava job都放在github actions中执行，将需要执行的job文件也存放在github actions所在的仓库里

下面的workflow实现的是每天在UTC时间1点从kernel官网获取源码并构建，构建完成后将kernel image发布到当前仓库的deploy分支，最后再通过lavaci命令，提交当前仓库中qemu-test目录下的lava job文件qemu-riscv64-helloworld-test.yaml到lava中执行

````
# Controls when the workflow will run
on:
  # Triggers the workflow on push or pull request events but only for the "main" branch
  # push:
  # pull_request:
  #   types:
  #     - closed
  schedule:
    - cron:  '0 1 * * *'

  # Allows you to run this workflow manually from the Actions tab
  workflow_dispatch:

# A workflow run is made up of one or more jobs that can run sequentially or in parallel
jobs:
  # This workflow contains a single job called "build"
  build-and-deploy:
    # The type of runner that the job will run on
    runs-on: ubuntu-latest

    # Steps represent a sequence of tasks that will be executed as part of the job
    steps:
      # Checks-out your repository under $GITHUB_WORKSPACE, so your job can access it
      - name: Checkout Kernel Source Code
        uses: actions/checkout@v3
        with:
          repository: torvalds/linux
          ref: master

      # Runs a single command using the runners shell
      - name: Install Dependency
        run: |
          sudo apt install make flex bison bc gcc-riscv64-linux-gnu git -y
          riscv64-linux-gnu-gcc -v
      # Runs a set of commands using the runners shell
      - name: Build
        run: |
          make ARCH=riscv defconfig
          make ARCH=riscv CROSS_COMPILE=riscv64-linux-gnu- -j $(nproc)
          mkdir kernel_image
          cp arch/riscv/boot/Image kernel_image
      
      # Runs a set of commands using the runners shell
      - name: Deploy
        uses: JamesIves/github-pages-deploy-action@v4.4.1
        with:
          ACCESS_TOKEN: ${{ secrets.ACCESS_TOKEN }}
          BRANCH: deploy
          FOLDER: kernel_image
      
      - name: Checkout Lava Job
        uses: actions/checkout@v3

      - name: Trggger Lava Job
        run: |
          sudo apt install lavacli -y
          lavacli --uri http://admin:${{ secrets.LAVA_TOKEN }}@192.168.1.100:8000/RPC2/ jobs submit ./qemu-test/qemu-riscv64-helloworld-test.yaml
````

其中:

admin:secrets.LAVA_TOKEN是存储在github中的可以访问lava的token，也就是上述3.3.2中在boards.yaml里设置的lava账号的用户名及其token

192.168.1.100:8000是lava web界面的url

workflow文档的例子存放在本仓库中的github-actions目录下，cicd.yml和cici_gitlab.yml的区别是前者将kernel image发布在当前仓库的指定分支，后者将kernel image发布到gitlab仓库的指定分支


参考：  
https://github.com/kernelci/lava-docker  
https://master.lavasoftware.org/static/docs/v2/index.html  
https://github.com/kernelci/kernelci-docker  
https://kernelci.org/docs/  
https://master.lavasoftware.org/static/docs/v2/lavacli.html?highlight=api













