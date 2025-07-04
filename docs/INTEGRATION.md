# Python3 #

The [integration/basic_client.py](integration/basic_client.py) gives a simple example of Python integration with the Ersilia Hub API.

The integration uses an anonymous session to submit a job, wait for the result and print to a CSV file.

```
python basic_client.py eos2m0f ../examples/smiles_100.csv smiles_100_output.csv
```

## To get active models from server ##

```
python basic_client.py print_models
```