import urllib2

data = open("sample2.txt").read()
#data = open("sample-output.txt").read()
response=urllib2.urlopen("http://127.0.0.1:8000/submit",data=data).read()

print(response)
