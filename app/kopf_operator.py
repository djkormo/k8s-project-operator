import time
import kopf
import kubernetes
import yaml
import json
import os
from environs import Env
from kubernetes.client.rest import ApiException
from pprint import pprint
import datetime
import random
import asyncio


@kopf.on.startup()
async def startup_fn_simple(logger, **kwargs):
  logger.info('Environment variables:')
  for k, v in os.environ.items():
    logger.info(f'{k}={v}')
    logger.info('Starting in 5s...')
    # use env variable to control loop interval in seconds

  await asyncio.sleep(5)

# for Kubernetes probes

@kopf.on.probe(id='now')
def get_current_timestamp(**kwargs):
    return datetime.datetime.utcnow().isoformat()

@kopf.on.probe(id='random')
def get_random_value(**kwargs):
    return random.randint(0, 1_000_000)


try:
  LOOP_INTERVAL = int(os.environ['LOOP_INTERVAL'])
except:
  LOOP_INTERVAL=30
  print(f"Variable LOOP_INTERVAL is not set, using {LOOP_INTERVAL}s as default")   
    
if LOOP_INTERVAL is None: 
    LOOP_INTERVAL = 30
        
try:
  EXCLUDED_NAMESPACES = os.environ['EXCLUDED_NAMESPACES']
except:
  EXCLUDED_NAMESPACES="kube-system,kube-public,kube-node-lease"
  print(f"Variable EXCLUDED_NAMESPACES is not set, using {EXCLUDED_NAMESPACES} as default")    

if EXCLUDED_NAMESPACES is None: 
  EXCLUDED_NAMESPACES = "kube-system,kube-public,kube-node-lease"

      
# check if namespace should be under operator control

def check_namespace(name,excluded_namespaces):
      
  namespace_list = list(excluded_namespaces)
  if name in namespace_list:
    print(f"Excluded namespace list: {namespace_list} ")    
    print(f"Excluded namespace found: {name}")
    return True
  else:
    return False  


# create namespace
def create_namespace(kopf,name,namespace,meta,spec,logger,api,filename):
  path = os.path.join(os.path.dirname(__file__), filename)
  tmpl = open(path, 'rt').read()
  text = tmpl.format(name=name, namespace=namespace)

  data = yaml.safe_load(text)
  kopf.adopt(data)

  ## Create namespace
  try:
    obj = api.create_namespace(
          body=data,
      )
    kopf.append_owner_reference(obj)
    logger.info(f"Namespace child is created: {obj}")
  except ApiException as e:
      logger.error("Exception when calling CoreV1Api->create_namespace: %s\n" % e)  
    
  # get annotations from parent object
  annotations=meta['annotations']
  
  # get labels from parrent object 

  labels=meta['labels']

  logger.debug(f"Project ANNOTATIONS {annotations} and LABELS {labels}\n")
 
  # Apply annotations to namespace
  try:
    obj = api.patch_namespace(
          name=name,
          body={"metadata": {"annotations": annotations} }
      )
  # Apply labels to namespace  
    obj = api.patch_namespace(
          name=name,
          body={"metadata": {"labels": labels}}
      )
    #logger.info(f"Namespace child is patched: {obj}")
  except ApiException as e:
      logger.error("Exception when calling CoreV1Api->patch_namespace: %s\n" % e)  

  return {'project-name': obj.metadata.name}

# replace namespace      
def replace_namespace(kopf,name,namespace,meta,spec,logger,api,filename):

  path = os.path.join(os.path.dirname(__file__), filename)
  tmpl = open(path, 'rt').read()

  # get annotations from parent object
  annotations=meta['annotations']
  # get labels from parent object
  labels=meta['labels'] 
  logger.debug(f"Project ANNOTATIONS {annotations} and LABELS {labels}\n")
 
  # mock data
  #labels = {"owner": "djkormo", "name": "project"}
  #labels = {'env': 'kubernetes', 'name': 'project', 'owner': 'djkormo', 'type': 'operator'}
  #labels=json.dump(labels)
  #annotations = {"description": "test","confirmation":"yes"}
  
  logger.debug(f"Project LABELS {labels} \n")
  
  # Apply annotations to namespace
  try:
    obj = api.patch_namespace(
          name=name,
          body={"metadata": {"annotations": annotations}}
      )
  # Apply labels to namespace
    obj = api.patch_namespace(
          name=name,
          body={"metadata": {"labels": labels}  }
      )
    #logger.info(f"Namespace child is patched: {obj}")
  except ApiException as e:
      logger.error("Exception when calling CoreV1Api->patch_namespace: %s\n" % e)  

# create resourcequota based on yaml manifest
def create_resourcequota(kopf,name,meta,spec,logger,api,filename):

  path = os.path.join(os.path.dirname(__file__), filename)
  tmpl = open(path, 'rt').read()

  resourcequotarequestscpu = spec['resourcequota'].get('resourcequotarequestscpu',1)
  if not resourcequotarequestscpu:
    raise kopf.PermanentError(f"resourcequotarequestscpu must be set. Got {resourcequotarequestscpu!r}.")

  resourcequotarequestsmemory = spec['resourcequota'].get('resourcequotarequestsmemory',1)
  if not resourcequotarequestsmemory:
    raise kopf.PermanentError(f"resourcequotarequestsmemory must be set. Got {resourcequotarequestsmemory!r}.")
    
  resourcequotalimitscpu=spec['resourcequota'].get('resourcequotalimitscpu',1)
    
  resourcequotalimitsmemory=spec['resourcequota'].get('resourcequotalimitsmemory',1)
  resourcequotacountjobsbatch=spec['resourcequota'].get('resourcequotacountjobsbatch',1)
  resourcequotacountingresses=spec['resourcequota'].get('resourcequotacountingresses',1)
  resourcequotapods=spec['resourcequota'].get('resourcequotapods',1)
  resourcequotaservices=spec['resourcequota'].get('resourcequotaservices',1)
  resourcequotaconfigmaps=spec['resourcequota'].get('resourcequotaconfigmaps',1)
  resourcequotapersistentvolumeclaims=spec['resourcequota'].get('resourcequotapersistentvolumeclaims',1)
  resourcequotareplicationcontrollers=spec['resourcequota'].get('resourcequotareplicationcontrollers',1)
  resourcequotasecrets=spec['resourcequota'].get('resourcequotasecrets',1)
  resourcequotaservicesloadbalancers=spec['resourcequota'].get('resourcequotaservicesloadbalancers',1)

  text = tmpl.format(name=name,resourcequotarequestscpu=resourcequotarequestscpu,
           resourcequotarequestsmemory=resourcequotarequestsmemory, 
           resourcequotalimitscpu=resourcequotalimitscpu,
           resourcequotalimitsmemory=resourcequotalimitsmemory,
           resourcequotacountjobsbatch=resourcequotacountjobsbatch,
           resourcequotacountingresses=resourcequotacountingresses,
           resourcequotapods=resourcequotapods,
           resourcequotaservices=resourcequotaservices,
           resourcequotaconfigmaps=resourcequotaconfigmaps,
           resourcequotapersistentvolumeclaims=resourcequotapersistentvolumeclaims,
           resourcequotareplicationcontrollers=resourcequotareplicationcontrollers,
           resourcequotasecrets=resourcequotasecrets,
           resourcequotaservicesloadbalancers=resourcequotaservicesloadbalancers
    )

  data = yaml.safe_load(text)
  try:
    obj = api.create_namespaced_resource_quota(
        namespace=name,
        body=data,
      )
    kopf.append_owner_reference(obj)
  except ApiException as e:
    logger.error("Exception when calling CoreV1Api->create_namespaced_resource_quota: %s\n" % e)
  kopf.adopt(data)

# replace resourcequota based on yaml manifest
def replace_resourcequota(kopf,name,meta,spec,logger,api,filename):

  path = os.path.join(os.path.dirname(__file__), filename)
  tmpl = open(path, 'rt').read()

  resourcequotarequestscpu = spec['resourcequota'].get('resourcequotarequestscpu',1)
  if not resourcequotarequestscpu:
    raise kopf.PermanentError(f"resourcequotarequestscpu must be set. Got {resourcequotarequestscpu!r}.")

  resourcequotarequestsmemory = spec['resourcequota'].get('resourcequotarequestsmemory',1)
  if not resourcequotarequestsmemory:
    raise kopf.PermanentError(f"resourcequotarequestsmemory must be set. Got {resourcequotarequestsmemory!r}.")
    
  resourcequotalimitscpu=spec['resourcequota'].get('resourcequotalimitscpu',1)
    
  resourcequotalimitsmemory=spec['resourcequota'].get('resourcequotalimitsmemory',1)
  resourcequotacountjobsbatch=spec['resourcequota'].get('resourcequotacountjobsbatch',1)
  resourcequotacountingresses=spec['resourcequota'].get('resourcequotacountingresses',1)
  resourcequotapods=spec['resourcequota'].get('resourcequotapods',1)
  resourcequotaservices=spec['resourcequota'].get('resourcequotaservices',1)
  resourcequotaconfigmaps=spec['resourcequota'].get('resourcequotaconfigmaps',1)
  resourcequotapersistentvolumeclaims=spec['resourcequota'].get('resourcequotapersistentvolumeclaims',1)
  resourcequotareplicationcontrollers=spec.get('resourcequotareplicationcontrollers',1)
  resourcequotasecrets=spec['resourcequota'].get('resourcequotasecrets',1)
  resourcequotaservicesloadbalancers=spec['resourcequota'].get('resourcequotaservicesloadbalancers',1)

  text = tmpl.format(name=name,resourcequotarequestscpu=resourcequotarequestscpu,
           resourcequotarequestsmemory=resourcequotarequestsmemory, 
           resourcequotalimitscpu=resourcequotalimitscpu,
           resourcequotalimitsmemory=resourcequotalimitsmemory,
           resourcequotacountjobsbatch=resourcequotacountjobsbatch,
           resourcequotacountingresses=resourcequotacountingresses,
           resourcequotapods=resourcequotapods,
           resourcequotaservices=resourcequotaservices,
           resourcequotaconfigmaps=resourcequotaconfigmaps,
           resourcequotapersistentvolumeclaims=resourcequotapersistentvolumeclaims,
           resourcequotareplicationcontrollers=resourcequotareplicationcontrollers,
           resourcequotasecrets=resourcequotasecrets,
           resourcequotaservicesloadbalancers=resourcequotaservicesloadbalancers
    )
    
  data = yaml.safe_load(text)
  try:
    obj = api.replace_namespaced_resource_quota(
        namespace=name,
        name=name,
        body=data,
      )
    
  except ApiException as e:
    logger.error("Exception when calling CoreV1Api->replace_namespaced_resource_quota: %s\n" % e)
  

def delete_resourcequota(kopf,name,spec,logger,api):
  try:
    obj = api.delete_namespaced_resource_quota(
        namespace=name,
        name=name
      )
    logger.debug(f"LimitRange child is deleted: {obj}")
  except ApiException as e:
    logger.error("Exception when calling CoreV1Api->delete_namespaced_resource_quota: %s\n" % e)


# create limitrange based on yaml manifest
def create_limitrange(kopf,name,meta,spec,logger,api,filename):
      
  try:    
    # get annotations from parent object
    annotations=meta['annotations']
  
    # get labels from parrent object 
    labels=meta['labels']
  
    logger.debug(f"Namespace {name} limitrange spec: {spec['limitRange']}\n")    
  except ApiException as e:
    logger.error("Exception when getting information from parent Project: %s\n" % e)
    return None  
    
      
  path = os.path.join(os.path.dirname(__file__), filename)
  tmpl = open(path, 'rt').read()
  
  maxcpu = spec['limitRange'].get('maxcpu',"20000m")
  maxmem = spec['limitRange'].get('maxmem',"30Gi")
  mincpu = spec['limitRange'].get('mincpu',"50m")
  minmem = spec['limitRange'].get('minmem',"50Mi")
  defaultcpu = spec['limitRange'].get('defaultcpu',"1000m")
  defaultmem = spec['limitRange'].get('defaultmem',"1000Mi")
  defaultrequestcpu = spec['limitRange'].get('defaultrequestcpu',"100m")
  defaultrequestmem = spec['limitRange'].get('defaultrequestmem',"100Mi")
  
  text = tmpl.format(name=name,
          maxmem=maxmem,
          maxcpu=maxcpu,
          mincpu=mincpu,
          minmem=minmem,
          defaultcpu=defaultcpu,
          defaultmem=defaultmem,
          defaultrequestcpu=defaultrequestcpu,
          defaultrequestmem=defaultrequestmem,
    )

  data = yaml.safe_load(text)
  try:
    obj = api.create_namespaced_limit_range(
        namespace=name,
        body=data,
      )
    kopf.append_owner_reference(obj)
  except ApiException as e:
    logger.error("Exception when calling CoreV1Api->create_namespaced_limit_range: %s\n" % e)
  kopf.adopt(data)

# replace limitrange based on yaml manifest
def replace_limitrange(kopf,name,meta,spec,logger,api,filename):
  # get annotations from parent object
  annotations=meta['annotations']
  
  # get labels from parrent object 
  labels=meta['labels']
  
  logger.debug(f"Project {name} limitrange spec: {spec['limitRange']} \n")    
  
  path = os.path.join(os.path.dirname(__file__), filename)
  tmpl = open(path, 'rt').read()
  maxcpu = spec['limitRange'].get('maxcpu',"20000m")
  maxmem = spec['limitRange'].get('maxmem',"30Gi")
  mincpu = spec['limitRange'].get('mincpu',"50m")
  minmem = spec['limitRange'].get('minmem',"50Mi")
  defaultcpu = spec['limitRange'].get('defaultcpu',"1000m")
  defaultmem = spec['limitRange'].get('defaultmem',"1000Mi")
  defaultrequestcpu = spec['limitRange'].get('defaultrequestcpu',"100m")
  defaultrequestmem = spec['limitRange'].get('defaultrequestmem',"100Mi")

  text = tmpl.format(name=name,maxmem=maxmem,
           maxcpu=maxcpu,
           mincpu=mincpu,
           minmem=minmem,
           defaultcpu=defaultcpu,
           defaultmem=defaultmem,
           defaultrequestcpu=defaultrequestcpu,
           defaultrequestmem=defaultrequestmem,
    )

  data = yaml.safe_load(text)
  try:
    obj = api.replace_namespaced_limit_range(
        namespace=name,
        name=name,
        body=data,
      )
    kopf.append_owner_reference(obj)
    logger.debug(f"LimitRange child is created: {obj}")
  except ApiException as e:
    logger.error("Exception when calling CoreV1Api->replace_namespaced_limit_range: %s\n" % e)
  kopf.adopt(data)  
  
# delete limitrange   
def delete_limitrange(kopf,name,spec,logger,api):
    
  try:
    obj = api.delete_namespaced_limit_range(
        namespace=name,
        name=name
      )
    logger.debug(f"LimitRange child is deleted: {obj}")
  except ApiException as e:
    logger.error("Exception when calling CoreV1Api->delete_namespaced_limit_range: %s\n" % e)


# create networkpolicy based on yaml manifest  
def create_networkpolicy(kopf,name,namespace,spec,logger,api,filename):
  path = os.path.join(os.path.dirname(__file__), filename)
  tmpl = open(path, 'rt').read()
  #logger.info(f" Network policy in namespace {namespace} file: {tmpl}")
  data = yaml.safe_load(tmpl)
  #logger.info(f" Network policy in namespace {namespace} file: {data}")
  try:
    obj = api.create_namespaced_network_policy(
        namespace=namespace,
        body=data,
      )
  except ApiException as e:
    logger.error("Exception when calling NetworkingV1Api->create_namespaced_network_policy: %s\n" % e)

# replace networkpolicy based on yaml manifest  
def replace_networkpolicy(kopf,name,namespace,logger,api,filename,policyname):
  path = os.path.join(os.path.dirname(__file__), filename)
  tmpl = open(path, 'rt').read()
  data = yaml.safe_load(tmpl)
  try:
    obj = api.replace_namespaced_network_policy(
        namespace=name,
        name=policyname,
        body=data,
      )
  except ApiException as e:
    logger.error("Exception when calling NetworkingV1Api->replace_namespaced_network_policy: %s\n" % e)


def delete_networkpolicy(kopf,namespace,policyname,logger,api):
        
  try:
    obj = api.delete_namespaced_network_policy(
        namespace=namespace,
        name=policyname
      )
    logger.debug(f"NetworkPolicy child is deleted: {obj}")
  except ApiException as e:
    logger.error("Exception when calling CoreV1Api->delete_namespaced_network_policy: %s\n" % e)


    
 

@kopf.on.resume('djkormo.github', 'v1alpha2', 'project')
@kopf.on.create('djkormo.github', 'v1alpha2', 'project')
# When updating object
@kopf.on.update('djkormo.github', 'v1alpha2', 'project')
@kopf.on.timer('djkormo.github', 'v1alpha2', 'project',interval=LOOP_INTERVAL,sharp=True)
def check_object_on_loop(spec, name, status, namespace,meta, logger, **kwargs):
    logger.info(f"Timer: {spec} is invoked")

    api = kubernetes.client.CoreV1Api()

    # check for excluded namespace

    if check_namespace(name=namespace,excluded_namespaces=EXCLUDED_NAMESPACES):
      return {'project-operator-name': namespace} 

    try: 
      api_response = api.list_namespace() 
      l_namespace=[]
      for i in api_response.items:
        logger.debug("Namespaces list: %s\t name:" %(i.metadata.name))
        l_namespace.append(i.metadata.name)
    except ApiException as e:
      logger.error("Exception when calling CoreV1Api->list_namespace: %s\n" % e)

    if name not in l_namespace:
      create_namespace(kopf=kopf,name=name,namespace=namespace,meta=meta,spec=spec,logger=logger,api=api,filename='namespace/namespace.yaml')
    else:
      replace_namespace(kopf=kopf,name=name,namespace=namespace,meta=meta,spec=spec,logger=logger,api=api,filename='namespace/namespace.yaml')
    

    # create or update resourcequota
    
    api = kubernetes.client.CoreV1Api()

    try: 
      api_response = api.list_namespaced_resource_quota(namespace=name) 
      l_resoucequota=[]
      for i in api_response.items:
        logger.debug("ResourceQuota namespace: %s\t name: %s" %
          (i.metadata.namespace, i.metadata.name))
        l_resoucequota.append(i.metadata.name)
    except ApiException as e:
      logger.error("Exception when calling CoreV1Api->list_namespaced_resource_quota: %s\n" % e)

    if name not in l_resoucequota:
      create_resourcequota(kopf=kopf,name=name,meta=meta,spec=spec,logger=logger,api=api,filename='resourcequota/resourcequota.yaml')
    else:
      replace_resourcequota(kopf=kopf,name=name,meta=meta,spec=spec,logger=logger,api=api,filename='resourcequota/resourcequota.yaml')
 
    # create or update limit range
  
    api = kubernetes.client.CoreV1Api()

    try: 
      api_response = api.list_namespaced_limit_range(namespace=name) 
      l_limitrange=[]
      for i in api_response.items:
        logger.debug("Limitrange namespace: %s\t name: %s" %
          (i.metadata.namespace, i.metadata.name))
        l_limitrange.append(i.metadata.name)
    except ApiException as e:
      logger.error("Exception when calling CoreV1Api->list_namespaced_limit_range: %s\n" % e)

    if name not in l_limitrange:
      create_limitrange(kopf=kopf,name=name,meta=meta,spec=spec,logger=logger,api=api,filename='limitrange/limitrange.yaml')
    else:
      replace_limitrange(kopf=kopf,name=name,meta=meta,spec=spec,logger=logger,api=api,filename='limitrange/limitrange.yaml')

    api = kubernetes.client.NetworkingV1Api()

    try: 
      api_response = api.list_namespaced_network_policy(namespace=name) 
      l_netpol=[]
      for i in api_response.items:
        logger.debug("NetworkPolicy namespace: %s\t name: %s" %
          (i.metadata.namespace, i.metadata.name))
        l_netpol.append(i.metadata.name) 
    except ApiException as e:
      logger.error("Exception when calling NetworkingV1Api->list_namespaced_network_policy: %s\n" % e)
  
  # create or update networkpolicy

    try:
        networkpolicylist = spec['networkPolicy']
    except KeyError:
        networkpolicylist = ['allow-all-in-namespace', 'allow-dns-access', 'default-deny-egress', 'default-deny-ingress']
        logger.debug("matching all networkpolicies.")
    logger.debug(f'Matching networkpolicy: {networkpolicylist}')
    
    
    if networkpolicylist is None: 
        networkpolicylist = ['allow-all-in-namespace', 'allow-dns-access', 'default-deny-egress', 'default-deny-ingress']

    logger.info(f'Matching networkpolicy: {networkpolicylist}')
  
    api = kubernetes.client.NetworkingV1Api()

    try: 
      api_response = api.list_namespaced_network_policy(namespace=name) 
      l_netpol=[]
      for i in api_response.items:
        logger.debug("NetworkPolicy namespace: %s\t name: %s" %
          (i.metadata.namespace, i.metadata.name))
        l_netpol.append(i.metadata.name) 
    except ApiException as e:
      logger.error("Exception when calling NetworkingV1Api->list_namespaced_network_policy: %s\n" % e)


   # update/patch networkpolicies
   
    for netpol in networkpolicylist:
      try:    
        policy_filename='networkpolicy/'+netpol+'.yaml' 
        if netpol not in l_netpol:
          create_networkpolicy(kopf=kopf,name=name,namespace=name,spec=spec,logger=logger,api=api,filename=policy_filename)
        else:
          replace_networkpolicy(kopf=kopf,name=name,namespace=name,logger=logger,api=api,filename=policy_filename,policyname=netpol)   
      except:
         logger.error(f"Cannot create/update networkpolicy {policy_filename} for {networkpolicylist}") 


  # create or update rolebinding or clusterrolebinding 
  
    logger.info(f'Checking RBAC roles in namespace {name}')
  
    api = kubernetes.client.RbacAuthorizationV1Api()
    
    try: 
      api_response = api.list_namespaced_role_binding(namespace=name) 
      l_rolebinding=[]
      for i in api_response.items:
        logger.debug("RoleBinding namespace: %s\t name: %s" %
          (i.metadata.namespace, i.metadata.name))
        l_rolebinding.append(i.metadata.name) 
    except ApiException as e:
      logger.error("Exception when calling RbacAuthorizationV1Api->list_namespaced_role_binding: %s\n" % e)


    logger.info(f'Checking RBAC cluster roles ')
    try: 
      api_response = api.list_cluster_role_binding() 
      l_clusterrolebinding=[]
      for i in api_response.items:
        logger.debug("ClusterRoleBinding : %s\t name: %s" %
          (i.metadata.namespace, i.metadata.name))
        l_clusterrolebinding.append(i.metadata.name) 
    except ApiException as e:
      logger.error("Exception when calling RbacAuthorizationV1Api->list_cluster_role_binding: %s\n" % e)


@kopf.on.delete('djkormo.github', 'v1alpha2', 'project')
def delete_fn(spec, name, status, namespace, logger, **kwargs):
    logger.info(f"Deleting: {spec}")
    
    
    # delete resourcequota 
    logger.info(f"Deleting resourcequota: {name}")
    
    api = kubernetes.client.CoreV1Api()

    try: 
      api_response = api.list_namespaced_resource_quota(namespace=name) 
      l_resoucequota=[]
      for i in api_response.items:
        logger.debug("ResourceQuota namespace: %s\t name: %s" %
          (i.metadata.namespace, i.metadata.name))
        l_resoucequota.append(i.metadata.name)
    except ApiException as e:
      logger.error("Exception when calling CoreV1Api->list_namespaced_resource_quota: %s\n" % e)

    if name in l_resoucequota:
      delete_resourcequota(kopf=kopf,name=name,spec=spec,logger=logger,api=api)

    
    
    # delete limit range 
    
    logger.info(f"Deleting limitrange: {name}")
    
        # create limitrange 
    api = kubernetes.client.CoreV1Api()

    try: 
      api_response = api.list_namespaced_limit_range(namespace=name) 
      l_limitrange=[]
      for i in api_response.items:
        logger.debug("Limitrange namespace: %s\t name: %s" %
          (i.metadata.namespace, i.metadata.name))
        l_limitrange.append(i.metadata.name)
    except ApiException as e:
      logger.error("Exception when calling CoreV1Api->list_namespaced_limit_range: %s\n" % e)

    if name in l_limitrange:
      delete_limitrange(kopf=kopf,name=name,spec=spec,logger=logger,api=api)
      
    # delete network policy
  
    
    api = kubernetes.client.NetworkingV1Api()

    try:
        networkpolicylist = spec['networkPolicy']
    except KeyError:
        networkpolicylist = ['allow-all-in-namespace', 'allow-dns-access', 'default-deny-egress', 'default-deny-ingress']
        logger.debug("matching all networkpolicies.")
    logger.debug(f'Matching networkpolicy: {networkpolicylist}')
    
  
    if networkpolicylist is None: 
        networkpolicylist = ['allow-all-in-namespace', 'allow-dns-access', 'default-deny-egress', 'default-deny-ingress']

    try: 
      api_response = api.list_namespaced_network_policy(namespace=name) 
      l_netpol=[]
      for i in api_response.items:
        logger.debug("NetworkPolicy namespace: %s\t name: %s" %
          (i.metadata.namespace, i.metadata.name))
        l_netpol.append(i.metadata.name) 
    except ApiException as e:
      logger.error("Exception when calling NetworkingV1Api->list_namespaced_network_policy: %s\n" % e)
      
    # delete network policy  
    for netpol in l_netpol:
      if netpol in networkpolicylist:    
        logger.info(f"Deleting network policy: {netpol}")    
        delete_networkpolicy(kopf=kopf,namespace=name,logger=logger,api=api,policyname=netpol) 
        
        
    
      
      