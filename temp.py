Class Solution():
  def __init__(self, solver):
    activeApproaches = where(solver.solution['x'] == 1)
    
    for i in activeApproach:
      type = solver.type[i]
      approach = solver.approach[i]
      setattr(self, type, approach)
      
    self.print('DEST', self.DestOps, self.DestPlan)
    self.print('Alt1', self.Alt1Ops, self.Alt1Plan)
    self.print('Alt2', self.Alt2Ops, self.Alt2Plan)
  
  def print(self, title, ops, plan):
    print('\n')
    print(title, ': ', ops.airportName)
    if plan.CAT1 == 1:
      cloudbase = '-'
    else:
      cloudbase = plan.cloudbase
    print('Plan:', plan.name, ' ', plan.RVR, 'm / ', cloudbase, 'ft')
    print('Ops: ', ops.name, ' ', ops.RVR, 'm / -ft')
    

   
    
    
      
