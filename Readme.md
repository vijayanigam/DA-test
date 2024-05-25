## Prerequsites
* python 3.10.0
* Static files should be present in files folder
* larger dataset is converted to parquet

## Flow
~~~
request:
{
        "end_time": bignint,
        "start_time": bigint 
}
~~~
~~~
 response:
{"file_path": "files/{}.xlsx"}
~~~

---
## To install the application
### Setup venv
~~~
python -m virtualenv venv --python=python
~~~
### Activate the env
~~~
source venv/bin/activate
~~~
### Install dependencies
~~~
pip install -r requirements.txt
~~~
---

## To run the application

~~~
uvicorn main:app
~~~