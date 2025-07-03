# MJ Automa 文生图任务

## 1. 获取任务
### 方法 POST
### URL: /api/get_mj_task
### Body
```json
{
    "prompt" : "",
    "oref" :   "http://***/aa.png",
    "ow"   :   200,
    "sref" :   ["http://***/aa.png","http://***/bb.png"],
    "sw"   :   100,
    "task_id" : 12545555
}
```
### Resp
```json
{
    "code":  0,
    "msg":  ""
}
```



## 2. 上报任务
### 方法 POST
### URL: /api/mj_task_report
### Body
```json
{
    "task_id" : 12545555,
    "code"    : 0,
    "images_url" :  ["http://***1.png","http://***2.png","http://***3.png"] 
}
```
### Resp
```json
{
    "code":  0,
    "msg":  ""
}
```