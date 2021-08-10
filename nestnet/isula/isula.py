import grpc, os
# import nestnet.isula.api_pb2
# import nestnet.isula.api_pb2_grpc
# import api_pb2,api_pb2_grpc
from nestnet.isula import api_pb2_grpc, api_pb2

from nestnet.log import info, error, warn, debug


# connect to isula rpc service:test ok
def connect():
    # connect to rpc service
    channel = grpc.insecure_channel('unix:///var/run/isulad.sock')
    #  rpc server
    runtime_stub = api_pb2_grpc.RuntimeServiceStub(channel)
    image_stub = api_pb2_grpc.ImageServiceStub(channel)
    return runtime_stub, image_stub


# get version of runtime:testok
def version():
    stub = connect()[0]
    response = stub.Version(api_pb2.VersionRequest())
    return response


def name_to_id(name):
    stub=connect()[0]

    list_con_resp = stub.ListContainers(api_pb2.ListContainersRequest())
    for container in list_con_resp.containers:
        if name == container.metadata.name:
            return container.id


def remove_container(container_id):
    stub = connect()[0]

    list_con_resp = stub.ListContainers(api_pb2.ListContainersRequest())

    for container in list_con_resp.containers:
        if container_id == container.id:
            stub.StopPodSandbox(api_pb2.StopPodSandboxRequest(pod_sandbox_id=container.pod_sandbox_id))
            stub.RemovePodSandbox(api_pb2.RemovePodSandboxRequest(pod_sandbox_id=container.pod_sandbox_id))
            return True


def is_container_running(container_id):
    stub = connect()[0]

    list_con_resp = stub.ListContainers(api_pb2.ListContainersRequest())
    for container in list_con_resp.containers:
        if container_id == container.id:
            return True
    return False


# get list of images:test ok
def pull_image(image_name):
    stub = connect()[1]
    if ':' not in image_name:
        image_name += ':latest'
    exist = False

    listimage_rep = stub.ListImages(api_pb2.ListImagesRequest())

    for image in listimage_rep.images:
        if image_name in str(image.repo_tags):
            exist=True
            break

    if not exist:
        try:
            info('image "%s" not found,Trying to pull image' % image_name)
            pull_rep = stub.PullImage(api_pb2.PullImageRequest(image=api_pb2.ImageSpec(image=image_name)))
            return True
        except BaseException:
            error("Pull error: %s" % pull_rep)
    else:
        return True


def clean():
    stub = connect()[0]
    list_Pod_resp = stub.ListPodSandbox(api_pb2.ListPodSandboxRequest())
    for Pod in list_Pod_resp.items:
        stub.StopPodSandbox(api_pb2.StopPodSandboxRequest(pod_sandbox_id=Pod.id))
        stub.RemovePodSandbox(api_pb2.RemovePodSandboxRequest(pod_sandbox_id=Pod.id))


# create and run podsandbox the create containers:
def runcontainer(name, config):
    stub = connect()[0]

    list_con_resp = stub.ListContainers(api_pb2.ListContainersRequest())

    for container in list_con_resp.containers:
        if name == container.metadata.name:
            # stub.RemoveContainer(api_pb2.RemoveContainerRequest(container.id))
            stub.StopPodSandbox(api_pb2.StopPodSandboxRequest(pod_sandbox_id=container.pod_sandbox_id))
            stub.RemovePodSandbox(api_pb2.RemovePodSandboxRequest(pod_sandbox_id=container.pod_sandbox_id))
            break

    pull_image(config['image'])

    # create pod
    pod_name=name+'sandbox'

    LinuxPodSecContext = api_pb2.LinuxSandboxSecurityContext(
        privileged=config['pod_privileged']
    )

    linuxPodCof = api_pb2.LinuxPodSandboxConfig(
        security_context = LinuxPodSecContext,
        sysctls = config['sysctls']
    )

    sandboxConfig = api_pb2.PodSandboxConfig(
        metadata=api_pb2.PodSandboxMetadata(name=pod_name, namespace="test"),
        dns_config=api_pb2.DNSConfig(servers=config['dns_servers'], searches=config['dns_searches']),
        hostname=config['hostname'],
        linux=linuxPodCof
    )
    podsandbox_rep = stub.RunPodSandbox(api_pb2.RunPodSandboxRequest(config=sandboxConfig))

    cap_add = api_pb2.Capability(
        add_capabilities=config['cap_add']
    )

    linuxContainerSecuContext = api_pb2.LinuxContainerSecurityContext(
        privileged=config['privileged'],
        capabilities=cap_add
    )

    linuxContainerRes = api_pb2.LinuxContainerResources(
        cpu_period=config['cpu_period'],
        cpu_quota=config['cpu_quota'],
        cpu_shares=config['cpu_shares'],
        memory_limit_in_bytes=config['mem_limit'],
        cpuset_cpus=config['cpuset_cpus']
    )

    linuxContainerconf = api_pb2.LinuxContainerConfig(
        resources=linuxContainerRes,
        security_context=linuxContainerSecuContext
    )

    # create container
    containerConfig = api_pb2.ContainerConfig(
        metadata=api_pb2.ContainerMetadata(name=name),
        image=api_pb2.ImageSpec(image=config['image']),
        command=config['cmd'],
        # devices=api_pb2.Device(container_path=config['device_con_path'],
        #                        host_path=config['device_host_path'],
        #                        permissions=config['device_permissions']),
        tty=config['tty'],
        linux=linuxContainerconf
    )

    container_resp = stub.CreateContainer(api_pb2.CreateContainerRequest(
        pod_sandbox_id=podsandbox_rep.pod_sandbox_id,
        config=containerConfig,
        sandbox_config=sandboxConfig,
    ))

    # start container
    start_resp = stub.StartContainer(api_pb2.StartContainerRequest(container_id=container_resp.container_id))

    return container_resp


def update_resourse(name,Resource):
    stub = connect()[0]

    container_id = name_to_id(name)

    default_res = {
        'cpu_quota': -1,
        'cpu_period': None,
        'cpu_shares': None,
        'cpuset_cpus': None,
        'mem_limit': None,
        'oom_score_adj': None,
        'cpuset_mems': None
    }

    default_res.update(Resource)

    ContainerResources = api_pb2.LinuxContainerResources(
        cpu_period=default_res['cpu_period'],
        cpu_quota=default_res['cpu_quota'],
        cpu_shares=default_res['cpu_shares'],
        memory_limit_in_bytes=default_res['mem_limit'],
        oom_score_adj=default_res['oom_score_adj'],
        cpuset_cpus=default_res['cpuset_cpus'],
        cpuset_mems=default_res['cpuset_mems']
    )

    stub.UpdateContainerResources(api_pb2.UpdateContainerResourcesRequest(container_id=container_id, linux=ContainerResources))


def get_status(container_id):
    stub = connect()[0]
    container_status = stub.ListContainers(api_pb2.ListContainersRequest(filter=api_pb2.ContainerFilter(id=container_id)))

    con_info= {'id': container_status.containers[0].id,
               'pod_sandbox_id': container_status.containers[0].pod_sandbox_id,
               'name': container_status.containers[0].metadata.name,
               'image': container_status.containers[0].image.image,
               'image_info': container_status.containers[0].image_ref,
               'created_at':container_status.containers[0].created_at}
    con_info.update(container_status.containers[0].annotations)

    return con_info


def inspect_image(imagename):
    stub=connect()[1]
    image=api_pb2.ImageSpec(image=imagename)
    imageinfo = stub.ImageStatus(api_pb2.ImageStatusRequest(image=image))


# if __name__=='__main__':
#     defaults = {
#             'privileged': False,
#             'pod_privileged': True,
#             'volumes': [],
#             'cpu_quota': -1,
#             'cpu_period': None,
#             'cpu_shares': None,
#             'cpuset_cpus': None,
#             'mem_limit': None,
#             'dns_servers': [],
#             'dns_searches': [],
#             'dns_options': [],
#             # 'device_con_path': '/',
#             # 'device_host_path': '/',
#             # 'device_permissions': 'r',
#             'mount': {},
#             'hostname': None,
#             'sysctls': {},
#             'cap_add': ['net_admin', ],
#             'cmd': ['/bin/sh', ],
#             'tty': True,
#             'image': 'alpine'
#         }
#     runcontainer('tt',defaults)
