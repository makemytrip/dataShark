Web Anomaly Detection
=====================

Purpose
-------

The main purpose of this use case was to help organizations, that can't implement proprietary solutions like a WAF or IPS, to detect a basic level of Bot or Scanner Attacks without having to write rules and work upon a purely machine learning based approach. Even organizations that implement a WAF and SIEM might be able to miss attacks from Smart Bots which mimic human like behavior and are able to circumvent Signature or Rule based systems, Web Anomaly Detection Use Case can help identify such attacks also.

Functionality
-------------

This use case is used to identify Anomalies in Web Traffic basis the response code. The code accepts an input stream of raw Apache Access Logs to find out in real time whether a User is a bot or not. The code aggregates the count of 2xx and 5xx response codes against a source IP, then finds out the distance between the current response code count and the predicted cluster center. This distance can then be used to alert on. 

Modifying the Use Case
----------------------

The use case comes shipped with a sample Apache access log file. This is not a standard access log file but is provided to get you started quickly with a streaming use case. In case you want to provide your own Apache access log file for training the model, change the `apache_access_logs_pattern` to use the correct regex.

Visualization
-------------

By default, the use case outputs the data to a CSV File. For visualizing this data, shipped along are Kibana Visualizations and Dashboard JSONs that can be imported in Kibana. For this, the output module should be elasticsearch. A sample conf for the elasticsearch output plugin can be like this:

```
[out_elasticsearch]
        host = 127.0.0.1
        port = 9200
        index_name = logstash-web-anomaly-detection
        doc_type = docs
        pkey = source_ip
        score = anomaly_score
        title = Web Anomaly Detection
        debug = false
```

Following is the screenshot of the Kibana Dashboard with this use case's data.

[![](https://makemytrip.github.io/images/dashboard.png)]()
