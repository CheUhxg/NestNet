# NestNet

## 安装
> 操作系统要求：**openEuler 21.03**和**Python3**

```bash
git clone -b master https://github.com/Constantine3/NestNet.git
cd NestNet
sudo bash util/install.sh -a
```

> 若中途停止重新运行**第三步**，需清空`NestNet`同级目录下的依赖文件夹。

## 运行

> 在`NestNet`目录下运行

```bash
# 无参数运行
./run-nestnet
# 使用isula作为终端
./run-nestnet --host isula
# 配置isula
./run-nestnet --host isula --config nestnet/examples/config_example.json
```

## 测试

> 进入`nestnet`测试网络是否连接成功

```bash
nestnet> pingall
*** Ping: testing ping reachability
h1 -> h2 
h2 -> h1 
*** Results: 0% dropped (2/2 received)
```

> 使用`exit`正常退出

```bash
nestnet> exit
```

