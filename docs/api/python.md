## Using within Python-Script
If you want to submit an energysystem from an external script, like a Website based on the Django-Framework, its possible with the python-request-package.

Therefore its recommend to call the function "/uploadJson". An simple example is given below.

```python
INRETENSYS_API_HOST = "http://localhost:8000"

requests.post(
    url=INRETENSYS_API_HOST+"/uploadJson/", 
    json=inret_em.json(), 
    params={'username': '', 'password': '', 'docker': True}
)
```

### Parameters
**JSON**: Contains the json-data from the energysystem, in the example the object from the class "InRetEnsysModel" is named "inret_em".

**PARAMS**: Containts a dictionary with three necessary arguments
- Username: The Auth-Username for the "Universitätsrechenzentrum Ilmenau"
- Password: The Auth-Password for the "Universitätsrechenzentrum Ilmenau"
- Docker: A Flag, if it is set to True, the Simulations are solve within docker instances and the arguments given before are not required
