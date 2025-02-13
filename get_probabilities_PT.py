# -*- coding: utf-8 -*-
"""
Created on Tue Jan  7 13:32:44 2025

@author: jaris
"""

import torch

from transformers import AutoTokenizer, AutoModel, pipeline
from transformers import  AutoModelForCausalLM
import numpy as np
import re



def softmax(x):
	exps = np.exp(x)
	return np.divide(exps, np.sum(exps))

# https://github.com/aub-mind/arabert
# pip install arabert

model_name = "PORTULAN/gervasio-7b-portuguese-ptpt-decoder"
model_name = "PORTULAN/gervasio-7b-portuguese-ptbr-decoder"
pt_preprocessor = PortuguesePreprocessor()
model = AutoModelForCausalLM.from_pretrained(model_name) 
tokenizer = AutoTokenizer.from_pretrained(model_name, use_fast = True)
model.eval()



def cloze_prob(text):
	whole_text_encoding = tokenizer.encode(text)
	# Parse out the stem of the whole sentence (i.e., the part leading up to but not including the critical word)
	text_list = text.split()
	stem = ' '.join(text_list[:-1])
	stem_encoding = tokenizer.encode(stem)
	# Run the entire sentence through the model. Then go "back in time" to look at what the model predicted for each token, starting at the stem.
	cw_encoding = whole_text_encoding[len(stem_encoding):]
 
	# Put the whole text encoding into a tensor, and get the model's comprehensive output
	tokens_tensor = torch.tensor([whole_text_encoding])
	
	with torch.no_grad():
		outputs = model(tokens_tensor)
		predictions = outputs[0]   

	logprobs = []
	# start at the stem and get downstream probabilities incrementally from the model(see above)
	start = -1-len(cw_encoding)
	for j in range(start,-1,1):
			raw_output = []
			for i in predictions[-1][j]:
					raw_output.append(i.item())
	
			logprobs.append(np.log(softmax(raw_output)))
			
	# this is just: raw_probabilities[i][token_index]
    
    
	conditional_probs = []
	for cw,prob in zip(cw_encoding,logprobs):
			conditional_probs.append(prob[cw])
	# now that you have all the relevant probabilities, return their product.
	# This is the probability of the critical word given the context before it.

	return np.exp(np.sum(conditional_probs))



##modified version

import torch
import numpy as np
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch.nn.functional as F 


def cloze_prob(text):
    # Tokenize the text and its stem
    whole_text_encoding = tokenizer.encode(text, add_special_tokens=False)
    text_list = text.split()
    stem = ' '.join(text_list[:-1])
    stem_encoding = tokenizer.encode(stem, add_special_tokens=False)
    cw_encoding = whole_text_encoding[len(stem_encoding):]

    # Convert to tensor
    tokens_tensor = torch.tensor([whole_text_encoding])

    # Get predictions
    with torch.no_grad():
        outputs = model(tokens_tensor)
        predictions = outputs.logits  # Shape: (batch_size, sequence_length, vocab_size)

    # Compute log probabilities for the entire sequence
    log_probs = F.log_softmax(predictions, dim=-1)  # Shape: (1, sequence_length, vocab_size)

    # Extract the log probabilities of the critical words
    conditional_probs = []
    for i, cw in enumerate(cw_encoding):
        token_log_prob = log_probs[0, -len(cw_encoding) + i, cw].item()  # Extract relevant log-prob
        conditional_probs.append(token_log_prob)

    # Return the product of probabilities
    return np.exp(np.sum(conditional_probs))


text= "O atleta consultou o ortopedista no hospital quando ele regressou da viagem a Itália."
score = cloze_prob(text)
print(text, score)
