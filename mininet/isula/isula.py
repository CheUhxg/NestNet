import grpc,re,random
import api_pb2
import api_pb2_grpc

# connect to isula rpc service:test ok
def connect():
    # 连接 rpc 服务器
    channel = grpc.insecure_channel('unix:///var/run/isulad.sock')
    # 调用 rpc 服务
    runtime_stub = api_pb2_grpc.RuntimeServiceStub(channel)
    image_stub = api_pb2_grpc.ImageServiceStub(channel)
    return runtime_stub,image_stub

# get version of runtime:test ok
def version():
    stub=connect()[0]
    response = stub.Version(api_pb2.VersionRequest())
    print( response)

# get list of containers:error failed to parse the sandbox name
def containers():
    stub=connect()[0]
    response = stub.ListContainers(api_pb2.ListContainersRequest())
    return response


# get list of images:test ok
def images():
    stub=connect()[1]
    response = stub.ListImages(api_pb2.ListImagesRequest())
    print(response)

# pull image:test ok
def pullimage():
    stub=connect()[1]
    response = stub.PullImage(api_pb2.PullImageRequest(image=api_pb2.ImageSpec(image="ubuntu")))
    print(response)

def createcontainer():
    random_number = random.randint(100000000,1000000000)
    resp = runpodsandbox(random_number)
    
    pattern = re.compile('"(.*)"')
    pod_sandbox_id = pattern.findall(str(resp))[0]

    stub=connect()[0]
    name = "ubuntu"+str(random_number)
    metadata = api_pb2.ContainerMetadata(name=name)
    image = api_pb2.ImageSpec(image="ubuntu")
    config = api_pb2.ContainerConfig(metadata=metadata,image=image)
    container_id = stub.CreateContainer(api_pb2.CreateContainerRequest(pod_sandbox_id=pod_sandbox_id, config=config))
    
    print(container_id)

def removecontainer(container_id):
    stub=connect()[0]
    response = stub.RemoveContainer(api_pb2.RemoveContainerRequest(container_id=container_id))
    print(response)

# get list of pod: test ok
def showpodsandbox():
    stub=connect()[0]
    response = stub.ListPodSandbox(api_pb2.ListPodSandboxRequest())
    print(response)

# create and run podsandbox:
def runpodsandbox(random_number):
    stub=connect()[0]
    sandboxConfig = api_pb2.PodSandboxConfig(
        metadata=api_pb2.PodSandboxMetadata(name="ubuntu-sandbox"+str(random_number), namespace="test"),
        dns_config=api_pb2.DNSConfig(servers=["3.3.3.3"], searches=["google.com"])
    )
    response = stub.RunPodSandbox(api_pb2.RunPodSandboxRequest(config=sandboxConfig))
    return response

def removepodsandbox(pod_sandbox_id):
    stub=connect()[0]
    response = stub.RemovePodSandbox(api_pb2.RemovePodSandboxRequest(pod_sandbox_id=pod_sandbox_id))
    print(response)

if  __name__ == '__main__':
    # images()
    # showpodsandbox()
    # pullimage()
    conts = str(containers())
    pattern = re.compile('  id: "(.*)"')
    for contid in pattern.findall(conts):
        print(contid)
        # removecontainer(contid)
    # createcontainer()
    # removepodsandbox('b2b6ae97195a84d5ffbce51f32b8761c0da60d1ec2167e834c31963b71d79553')