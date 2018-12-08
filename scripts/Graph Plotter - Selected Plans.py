
# coding: utf-8

# In[29]:


import os
import csv
import numpy as np
import matplotlib.pyplot as plt


# In[30]:


alpha = 0.00
beta = 0.65
scenario='case2'
output_folder = '../output/%s-%.2f-%.2f'%(scenario,alpha,beta)


# In[31]:


n_plans = 16
n_agents = 4000
epos_iterations = 40


# In[32]:


hist = [0]*n_plans
plot_time = 0
plans_folder = os.path.join(output_folder,"t_%d"%plot_time,"traffic")
included = []
for agent in range(n_agents):
    agent_plans_file = os.path.join(plans_folder,'agent_%d.plans'%agent)
    f = open(agent_plans_file,'r')
    if f.readline()[0]!='0':
        included.append(agent)
    f.close()
selected_plans_file = os.path.join(output_folder,"t_%d"%plot_time,'selected-plans.csv')
with open(selected_plans_file, mode='r') as infile:
    reader = csv.reader(infile)
    for i in range(epos_iterations):
        next(reader)

    for rows in reader:
        selected_plans = rows[2:]

        for agent in included:
            hist[int(selected_plans[agent])]+=1
        break


# In[33]:


freq = [x*1.0/sum(hist) for x in hist]
print(freq)
print(included)
# In[34]:


color = [x / 255 for x in [255,76,76]]
plt.bar(list(range(n_plans)),freq,width=1,color=color)
plt.xticks(list(range(n_plans)), list(range(n_plans)))
plt.xlabel('Plan index')
plt.ylabel('Frequency')
plt.title('Selected plans: alpha=%.2f, beta=%.2f'%(alpha,beta))
plt.savefig('selected-plans-t_%d-%.2f-%.2f.png'%(plot_time,alpha,beta))


# In[15]:


len(included)

