import configparser, json,urllib.request
import psycopg2


def postgres_conn(conn_url, unix_timestamp, longa, lat):
    try:
        connection_url = conn_url

        # Establish the connection
        connection = psycopg2.connect(connection_url)

        if connection:
            cursor = connection.cursor()
            query = "INSERT INTO api_table (timestamp, longitude, latitude) VALUES (TO_TIMESTAMP(%s), %s, %s)"
            cursor.execute(query, (unix_timestamp, longa, lat))
            connection.commit()
            cursor.close()
            connection.close()
        else:
            raise Exception("Failed to connect to the database")
    except psycopg2.Error as e:
        raise Exception(f"Database error - {e}")
    
def apitodb(conn_url, api_url):
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
        
def read_db_config(filename, section):
    try:
      parser = configparser.ConfigParser()
      parser.read(filename)
      config = parser[section]

      return config['db_url'], config['api_url']

    except configparser.Error as e:
      error_message = {"configparserError": f"{str(e)}"} # Error can be viewed on Cloudwatch for analysis
      return error_message


def lambda_handler(event, context):
  filename,section ='config/api_lambda.config', 'aws_creds'
  conn_url, api_url = read_db_config(filename,section)
  data = apitodb(conn_url, api_url)

  if "LambdaError" in data:
    return data # Error can be viewed on Cloudwatch for analysis
  else:
     return {"Success":"Lambda Succesfully Executed"}  

