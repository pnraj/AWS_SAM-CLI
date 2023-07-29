

## DEVELOP, TEST, DEPLOY `AWS LAMBDA` USING `SAM-CLI`

## Objectives:
- Using `SAM CLI` plug-in with `VS CODE EDITOR` - Develop _`lambda function`_ locally using Python to Call External Rest API and Connect To Postgres Database,  
- Externalize API endpoints, Postgres Database credentials and
environment-related configurations in `Configuration file`,
- Test Deploy the build Using Docker Desktop __`sam local invoke`__,
- Deploy the Build into AWS using SAM CLI __`sam deploy`__

## Pre-requisite:
- __AWS Account__ with `Admin Access` or Full Access for `CloudFormation`, `s3`, `Lambda`, `EventBridge`
- Install and Configure `AWS CLI` 
- Install `SAM CLI`, `VS CODE EDITOR`, `Docker Desktop`
- Install `Python 3.11`
- Pip install `pycong2.binary`,
  - Other Inbuilt lib used are `configparser`, `json` , `urllib.request`

## Develop:
#### `Call_API`:
- Call Api using `urllib.request` and loads the data as `json` using `json.loads`
<!--Using urllib.request because api is light weight-->

```py
    try:
        response = urllib.request.urlopen(api_url)
        dic = json.loads(response.read().decode())
        longa, lat = dic["iss_position"]["longitude"], dic["iss_position"]["latitude"]
        unix_timestamp = dic["timestamp"]
        message = dic['message']
        if message == "success":
            postgres_conn(conn_url, unix_timestamp, longa, lat )
            return {"Message":"Successfully Inserted"}
    except Exception as e:
        error_message = {"LambdaError": f"{str(e)}"} # Error can be viewed on Cloudwatch for analysis
        return error_message
```

#### `Insert Into Psql DB`:
- Api is Inserted into DB using `postgres_conn` function
  
``` py
    try:
        connection_url = conn_url

        # Establish the connection
        connection = psycopg2.connect(connection_url)

        if connection:
            cursor = connection.cursor()
            query = """INSERT INTO 
            api_table (timestamp, longitude, latitude) VALUES (TO_TIMESTAMP(%s), %s, %s)"""
            cursor.execute(query, (unix_timestamp, longa, lat))
            connection.commit()
            cursor.close()
            connection.close()
        else:
            raise Exception("Failed to connect to the database")
    except psycopg2.Error as e:
        raise Exception(f"Database error - {e}")

```

#### `CONFIG FILE`:
- All the Required API and Database credentials are kept in single file`config/api_lambda.config`
- Using this file we can Easily Update Credentials Based on the Environment

```config
    [aws_creds]

    # edit the db_url accordingly
    db_url = postgres://myuser:mypassword@localhost:5432/mydb

    # api used in this project(open source) 
    api_url = http://api.open-notify.org/iss-now.json

```
- Config get imported into script using `configparser`(python inbuilt lib) 

```py
    def read_db_config(filename, section):
        try:
        parser = configparser.ConfigParser()
        parser.read(filename)
        config = parser[section]

        return config['db_url'], config['api_url']

        except configparser.Error as e:
        error_message = {"configparserError": f"{str(e)}"} # Error can be viewed on Cloudwatch for analysis
        return error_message
```

#### `SAM CLI` TEMPLATE:
- Using _SAM CLI_ we can Create/Update Resourse Locally
- _EventBridge Rule_ is added as Trigger for lambda as 1 Min Interval
- Set Timeout as 10 seconds and Memorysize as 1gb / 1024 mb

```yaml

    AWSTemplateFormatVersion: '2010-09-09'
    Transform: 'AWS::Serverless-2016-10-31'

    Globals:
    Function:
        Timeout: 10
        MemorySize: 1024  # 1GB RAM (in MB)

    Resources:
    MyLambdaFunction:
        Type: 'AWS::Serverless::Function'
        Properties:
        CodeUri: fetch_api/
        Handler: api_function.lambda_handler
        Runtime: python3.11
        Architectures:
            - x86_64 
        
    MyEventRule:
        Type: AWS::Events::Rule
        Properties:
        ScheduleExpression: rate(1 minute)  # Trigger every 1 minute
        State: DISABLED  # The rule will be created in a disabled state
        Targets:
            - Arn: !GetAtt MyLambdaFunction.Arn
            Id: TargetFunction

```

### BUILD:
- Using `sam build` in the dir, where `template.yaml` is present
- SAM cli will build the setup for the code
  
<p align="center">
  <img src="others\screenshots\build.png" alt="Alt Text">
</p>

### TEST:
- Testing the Build locally using `Docker` and `SAM CLI` >> `sam local invoke`
- If image is not present in `Docker` it will _pull_ the required image and _test_ the build

<p align="center">
  <img src="others\screenshots\test.png" alt="Alt Text">
</p>

### DEPLOY:
- After Testing the Build, We can deploy into `AWS` using `sam deploy --guided`
- If the Build is deployed for the first time we should use `--guided`, otherwise we can use `sam deploy` for updating the template or other config
- From the `SAM CLI` template `AWS CloudFormation` will create Needed Permission and Role
  
<p align="center">
  <img src="others\screenshots\deploy_1.png" alt="Alt Text">
</p>

- After Acessing the needed resourses it will promt the confirmation before finalising the `deployment`

<p align="center">
  <img src="others\screenshots\deploy_2.png" alt="Alt Text">
</p>

- After Deploying into `AWS`, Eventbridge rule can be activated using `AWS CLI `or `CONSOLE`
- Using `AWS CLI` we can activate it by
  - First get the list of Event Rules in aws using
  
   ```
   aws events list-rules --query 'Rules[].Name'
   ```
  - Output will look like this or based on the number of rules available in your aws account
  ```
  [
    "MyLambdaStack-MyEventRule-18R5318AQ8PQD"
  ]
  ```
  - Next using the name which we created while deployment we can activate it 
  ```
  aws events enable-rule --name <rule-name>
  ```

