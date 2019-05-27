from hopcroftkarp import HopcroftKarp
import numpy as np
import random
class agent:
    '''
    A wrapper class for keeping track of match preferences.
    '''
    def __init__(self, agent_id, preferences):
        self.agent_id=agent_id
        self.preferences=preferences
        self.count=0

class goods_info:
    '''
    A wrapper class containing information for goods.
    '''
    def __init__(self, goods_id, pairs=None):
        self.id=goods_id
        self.pairs=pairs

        self.label=False
        
        
class node:
    '''
    Node for linked list.
    '''
    def __init__(self, head, child=None):
        self.head=head
        self.child=child
    def __str__(self):
        return "node("+str(self.head)+","+str(self.child)+")"
        
        
        
#linked list
class ll:
    '''
    Linked list.
    '''
    def __init__(self, head, child=None):
        self.head=head
        self.child=child
        
    def removeHead(self):
        '''
        Remove the head of linked list.
        '''
        item=self.head
        if self.child:
            self.head=self.child.head
            self.child=self.child.child
        else:
            self.head=None
        return item
        
    def append(self, data):
        '''
        Append data into linked list.
        '''
        if self.head:
            value=self.head
            nxt=self.child
            self.head=data
            self.child=node(value, nxt)
        else:
            self.head=data
    def __str__(self):
        '''
        Print linked list.
        '''
        return "ll("+str(self.head)+","+str(self.child)+")"
        
        
        
def basic_hopcroftkarp(agents):
    '''
    [Agents]->{agent_id:goods_id}
    
    Classic Hopcroft-Karp algorithm for generating maximum matching.
    '''
    preference={}
    agent_index=[]
    for agent in agents:
        preference[agent.agent_id]=agent.preferences
        agent_index.append(agent.agent_id)
    allocation=HopcroftKarp(preference).maximum_matching()
    allocation={key:allocation[key] for key in allocation if key in agent_index}
    
    return allocation
    


def Lh(agents, matching, good):
    '''
    ({agent_id:agent}, {agent_id:good_id}, {goods}) -> Linked list
    
    Helper function for the second phase of the algorithm.
    
    Generating linked list, which contains ranking information of goods.
    '''
    
    lst=ll(None, None)
    for agent in matching:
        if good in agents[agent].preferences:
            lst.append((agent, agents[agent].preferences.index(good)))
    return lst
    

def phase_2(agents, matching, goods):
    '''
    ({agent_id:agent}, {agent_id:good_id}, {goods}) -> {agent_id:good_id}
    
    Second phase of the algorithm.
    
    Transform current matching into a trade-in free matching.
    
    For each unmatched item, if it has higher ranking than current matching,
    assign this item to that agent, then free the original item.If this item 
    appear in any agent's preference list, push it to stack.
    Repeat doing it until there is no more adjustment.
    '''
    possible_item=[]
    for agent_index in agents:
        possible_item+=agents[agent_index].preferences
    #initialization:
    unmatched_goods=list(set(goods)-set(matching.values()))
    S=[]
    for good in unmatched_goods:
        if good in possible_item:
            S.append(goods_info(good, Lh(agents, matching, good)))
        else:
            pass
    #loop:
    while S!=[]:
        item=S.pop()
        #each pair has format (a, r), where a is the agent's id and r is the 
        #rank for the given good in agent's preference list
        pair=item.pairs.removeHead()
        if pair!=None:
            if pair[1] < agents[pair[0]].preferences.index(matching[pair[0]]):
                free_good=matching[pair[0]]
                matching[pair[0]]=item.id
                #update information contained in goods
                free_good_info_list=Lh(agents, matching, free_good)
                if free_good_info_list.head!=None:
                    S.append(goods_info(free_good, free_good_info_list))
    
    return matching
    
    

def phase_3(agents, matching, goods):
    '''
    ({agent_id:agent}, {agent_id:good_id}, {goods}) -> {agent_id:good_id}
    
    Third phase of the algorithm.
    
    Transform current matching into a coalition-free matching using the idea of 
    Top Trading Cycle Algorithm. Exchange matched goods within matched agents.
    '''
    #initialization
    goods_collection={}
    for good in goods:
        goods_collection[good]=goods_info(good)
        if good in matching.values():
            goods_collection[good].label=False
        else:
            goods_collection[good].label=True

    reverse_matching={matching[key]:key for key in matching}
    

    exchangable_agent={agent_index:agents[agent_index].preferences[0] \
                        for agent_index in matching \
            if agents[agent_index].preferences.index(matching[agent_index])!=0}
    #loop over all exchangable agents
    for agent in exchangable_agent:
        if len(exchangable_agent)==1:
            return matching
        else:
            P=[agent]
            while P!=[]:
                a=P.pop()
                #find the most preferred unlabelled good in a's preference list (if exists)
                p_a_list=[i for i in agents[a].preferences if goods_collection[i].label==False]
                if p_a_list!=[]:
                    p_a=p_a_list[0]
                    #if count==2, there is a cycle
                    if agents[a].count==2:
                        #if cycle occurs, solve the cycle
                        C=P
                        #make it easier to swap goods
                        C.reverse()
                        #swap goods within cycle
                        for i in range(len(C)-2):
                            temp=matching[C[i]]
                            matching[C[i]]=matching[C[i+1]]
                            matching[C[i+1]]=temp
                            reverse_matching[matching[C[i]]]=C[i]
                            reverse_matching[matching[C[i+1]]]=C[i+1]
                        #update goods status
                        for aa in C:
                            goods_collection[matching[aa]].label=True
                            agents[aa].count=0
                            temp=P.pop()
                    
                    elif p_a==matching[a]:
                        goods_collection[p_a].label=True
                        agents[a].count=0
                    else:
                        P.append(a)
                        aa=reverse_matching[p_a]
                        agents[aa].count+=1
                        P.append(aa)
                else:
                    continue
    return matching
    

        
    

def Maximum_Pareto_optimal_matching(goods, agents):
    '''
    ({goods}, [agents]) -> {agent_id:goods_id}
    
    Main function for maximum pareto optimal matching algorithm.
    '''
    #Generate a collection of agents used in the second and third phase of algorithm
    agent_dict={agent.agent_id:agent for agent in agents}
    #First phase of the algorithm, constructing a maximum matching
    phase_1_result=basic_hopcroftkarp(agents)
    #Second phase of the algorithm, convert current matching into a trade-in free matching
    phase_2_result=phase_2(agent_dict, phase_1_result, goods)
    #Third phase of the algorithm, convert current matching into a coalition-free matching.
    final_allocation=phase_3(agent_dict, phase_2_result, goods)
    
    return final_allocation


def auto_tester(agents_name, num_test):
    '''
    agents is a list of agents names
    '''
    result=[]
    for test in range(num_test):
        num_agents=random.randint(1,26)
        num_goods=random.randint(1,10)
        agents=[]
        agents_set=list(set(np.random.choice(agents_name, num_agents)))
        goods=[j for j in range(num_goods)]
        for agent_index in range(len(agents_set)):
            size=random.randint(0,num_goods)
            sample=np.random.choice(goods, size)
            agents.append(agent(agents_set[agent_index], list(set(sample))))
            #return agents, goods
        try:
            results=Maximum_Pareto_optimal_matching(goods, agents)
            result.append(True)
        except:
            return agents, goods
            result.append(False)
    print result.count(True), result.count(False)
    return None, None
        
        
    


if __name__== "__main__":
    #examples
    goods={1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20}
    agents=[agent('a', [6,2,9,17,2,4,1]), agent('b', [6,8,1,2,5,3]), agent('c',[6,4,3,2,6]), \
            agent('d', [6,3,2,14,5]), agent('e', [6,5,7,8,3,4])]

    #print basic_hopcroftkarp(agents)
    #print(final)
    agents_name=['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l','m','n',\
                'o','p','q','r','s','t','u','v','w','x','y','z']
    #print 
    final=Maximum_Pareto_optimal_matching(goods, agents)
    #agents,goods=auto_tester(agents_name, 20)