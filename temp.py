Class 


Class Solution():
  def __init__(self, solver):
    self.Dest = '-'
    self.Alt1 = '-'
    self.Alt2 = '-'
    self.DestOps = '-'
    self.DestPlan = '-'
    self.Alt1Ops = '-'
    self.Alt1Plan = '-'
    self.Alt2Ops = '-'
    self.Alt2Plan = '-'
    self.DestOpsValues = '-'
    self.DestPlanValues = '-'
    self.Alt1OpsValues = '-'
    self.Alt1PlanValues = '-'
    self.Alt2OpsValues = '-'
    self.Alt2PlanValues = '-'
    
    activeApproaches = where(solver.solution['x'] == 1)
    for i in activeApproach:
      type = solver.type[i]
      if  type == 'DestOps':
        self.Dest = solver.???
        self.DestOps = solver.approach[i].name
        self.DestOps = solver.approach[i].RVR
        
      eif type == 'DestPlan':
      
      eif type == 'Alt1Ops':
      
      eif type == 'Alt1Plan':
      
      eif type == 'Alt2Ops':
      
      eif type == 'Alt2Plan':
      
 
 def print(self):
    
    values = {}
    
    
      
