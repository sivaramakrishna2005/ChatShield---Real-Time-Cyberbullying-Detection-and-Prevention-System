from flask import Flask
from flask.wrappers import Request
from flask import request
from sklearn.feature_extraction.text import TfidfVectorizer
import pickle
import os

app = Flask(__name__)

def process_msg(msg):
    if msg == "hi":
        response = "Hello, Welcome to the cyberbullying detection bot!"
    else:
        # print(msg)
        msg = [msg]
        
        # Use local files placed with this script (relative paths) so the service runs on any machine
        base_dir = os.path.dirname(__file__)

        # List of stopwords
        stopwords_path = os.path.join(base_dir, "stopwords.txt")
        with open(stopwords_path, "r", encoding="utf-8") as my_file:
            content = my_file.read()
        content_list = content.split("\n")

        # Load vocabulary and model from files in the same folder
        vocab_path = os.path.join(base_dir, "tfidf_vector_vocabulary.pkl")
        vocab = pickle.load(open(vocab_path, "rb"))

        tfidf_vector = TfidfVectorizer(stop_words=content_list, lowercase=True, vocabulary=vocab)
        # Fit-transform the incoming message using the provided vocabulary
        data = tfidf_vector.fit_transform(msg)
        print(data)
        model_path = os.path.join(base_dir, "LinearSVC.pkl")
        model = pickle.load(open(model_path, 'rb'))
        pred = model.predict(data)
        response = str(pred[0])
        print(response)
        if(response=='1'):
            response = "Output from my ML Model :- bullying"
        else:
            response = "Output from my ML Model :- non-bullying"
            

    return response 

# Testing for postman

@app.route("/testing", methods = ["POST"])
def testing():
    f=request.form 
    print(f['Body'])
    msg=f['Body']
    sender=f['From']
    print(msg)
    response = process_msg(msg)
    return response,200