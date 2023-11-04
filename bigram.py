
import torch
import torch.nn as nn
from torch.nn import functional as F


batch_size = 4 # no fo independendent sequences processed parallel
block_size = 8 # max length of context for prediction
max_iters = 3000
eval_interval = 300
learning_Rate = 1e-2
device = 'cuda' if torch.cuda.is_available() else 'cpu'
eval_iters = 200
# ----------------------------------------------------------

torch.manual_seed(1337)


with open('input.txt','r',encoding='utf-8') as f:
  text = f.read()

#unique characters in text
chars = sorted(list(set(text)))
vocab_size = len(chars)
print(''.join(chars))
print(vocab_size)

#tokenize (chars to numbers)
stoi = {ch:i for i,ch in enumerate(chars)}
itos = {i:ch for i,ch in enumerate(chars)}
encode = lambda s: [stoi[c] for c in s] #take string and create list from index in stoi set
decode = lambda l: ''.join([itos[i]for i in l]) #take list of numbers and join chars from itos set to string

print(encode('Hallo du'))
print(decode(encode('Hallo du')))

#encode text, save to troch.Tensor, train and test split
data = torch.tensor(encode(text), dtype=torch.long)
n = int(0.9*len(data))
train_data = data[:n]
val_data = data[n:]


# create random selected 8 char list (context) and their respective 8 char set offset by one (targets)
# 4 pieces each (batch_size)


def get_batch(split):
  data = train_data if split =='train' else val_data
  ix = torch.randint(len(data) - block_size, (batch_size,))
  x = torch.stack([data[i:i+block_size] for i in ix])
  y = torch.stack([data[i+1:i+block_size+1] for i in ix])
  x,y = x.to(device) y.to(device)
  return x,y

xb,yb = get_batch('train')
print('inputs:')
print(xb.shape)
print(xb)
print('targets:')
print(yb.shape)
print(yb)

print('--------------------------------------')

for b in range (batch_size):
  for t in range(block_size):
    context = xb[b, :t+1]
    target = yb[b,t]
    print(f"when input is {context} the target is: {target}")

print(f"input: \n {xb}")


#Bigramm Language Model
class BigramLanguageModel(nn.Module):

  def __init__(self, vocab_size):
    super().__init__()
    #each token directly reads off the logits for the next token from a lookup table
    self.token_embedding_table = nn.Embedding(vocab_size, vocab_size)

  def forward(self, idx, targets=None):

    #idx and targets are bot (B,T) tensor of integers
    logits = self.token_embedding_table(idx) #(Batch,Time,Channel)

    if targets is None:
      loss = None
    else:
      B,T,C = logits.shape
      logits = logits.view(B*T,C)
      targets = targets.view(B*T)
      loss = F.cross_entropy(logits, targets)

    return logits, loss

  def generate(self, idx, max_new_tokens):
    #idx is (Batch, Time) array of indices in the current context
    for _ in range(max_new_tokens):
      #get the predictions
      logits, loss = self(idx)
      #only last time stamp
      logits = logits[:,-1,:] #becomse (Batch, Channel)
      #apply softmax to get the probabilities
      probs = F.softmax(logits, dim=1) #(Bacth, Channel)
      #sample from the distribution
      idx_next = torch.multinomial(probs, num_samples=1) # (Batch,1)
      #append sampled index to the running sequence
      idx = torch.cat((idx, idx_next), dim=1) #(Batch, Time+1)

    return idx


model = BigramLanguageModel(vocab_size)
m = model.to(device)



#PyTorch Optimizer
optimizer = torch.optim.AdamW(m.parameters(), lr=1e-3)

batch_size=32
for steps in range(1000):

  #sample a batch of data
  xb,yb = get_batch('train')

  #evaluate the loss
  logits, loss = m(xb,yb)
  optimizer.zero_grad(set_to_none=True)
  loss.backward()
  optimizer.step()

context = torch.zeros((1,1), dtype=torch.long, device=device)
print(decode(m.generate(context, max_new_tokens=500)[0].tolist()))

