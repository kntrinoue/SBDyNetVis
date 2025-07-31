import os
import pandas as pd
from basico import *
from SBDyNetVis.make_dynet import MakeDyNet
import shlex
# from basico import biomodels

def biomodels2dynet(model_inf, start_time=0, end_time=100, steps=10000, localCode=False):
  model = ModelManager(model_inf)
  model.set_simulation_conditions( start_time, end_time, steps)
  model.run_simulation()
  if model.error == 1:
    return None, None
  print("Simulation done")

  timecourse_data = pd.concat([model.simulation_results.species_values, model.simulation_results.reaction_values], axis=1)
  diagram_data = pd.DataFrame(model.network.edges)
  output_dir = "./"+model_inf
  if not os.path.exists(output_dir):
    os.makedirs(output_dir)
  timecourse_data.to_csv(output_dir+"/"+model_inf+"_timecourse.csv", index_label="Time")
  diagram_data.to_csv(output_dir+"/"+model_inf+"_diagram.csv", index=False)
  
  timecourse_data = pd.read_csv(output_dir+"/"+model_inf+"_timecourse.csv")
  diagram_data = pd.read_csv(output_dir+"/"+model_inf+"_diagram.csv")
  dynet = MakeDyNet(timecourse_data, diagram_data, modelName=model_inf, localCode=localCode)
  dynet.run()
  # print("Files are generated in " + os.path.realpath(output_dir))

  return timecourse_data, diagram_data



class CopasiSolver():
  def __init__(self):
    self.solverlist = {'Deteministic (LSODA)':'lsoda', 
                      'Deteministic (RADAU5)':'radau5', 
                      'Stochastic (Gibson+Bruck)':'stochastic', 
                      'Stochastic (Direct method)':'directMethod', 
                      'Stochastic (tauleap)':'tauleap', 
                      'Stochastic (adaptivesa)':'adaptivesa', 
                      'Hybrid (Runge-Kutta)':'hybrid', 
                      'Hybrid (LSODA)':'hybridlsoda', 
                      'Hybrid (RK-45)':'hybridode45', 
                      'SDE solver(RI5)':'sde'}
    self.solver = 'lsoda'
    self.startTime = 0
    self.endTime = 100
    self.ninvertals = 10000

    #lsoda
    self.atol = 1e-12
    self.rtol = 1e-6
    self.maxinternalsteps = 100000
    self.maxinternalstepsize = 0

class SimulationResults():
  def __init__(self):
    self.species_values = dict()
    self.reaction_values = dict()

  
# For network visualization
class NetworkManager():
  def __init__(self):
    self.nodes = []
    self.edges = [] # {reaction name: (tcID, src, tar, type, label)} 

# For simulation parameters
class BasicoDSManager():
  def __init__(self):
    self.model = None
    self.model_info = None
    self.species = {}
    self.reactions = {}
    self.functions = {}
    self.parameters = {}

# For math model, network and simulation
class ModelManager():
  def __init__(self, model_inf):
    
    
    self.simulation_results = SimulationResults() # simulation results
    self.basico = BasicoDSManager() # model parameters
    self.simulation_conditions = CopasiSolver() # simulation conditions
    self.changed_parameters = dict() # changed parameters for re-simulation
    self.network = NetworkManager() # network information
    self.model_inf = model_inf # model information
    self.modelsource = None # fileformat of the model
    self.error = 0 # error flag, 0: no error, 1: error

    if self.model_inf is None:
      print("No model information")
    else:
      if os.path.isfile(self.model_inf):
        if self.model_inf.endswith(".cps"):
          self.modelsource = "copasi"  
      elif self.model_inf.startswith("BIOMD"):
        self.modelsource = "Biomodels"

  def set_simulation_conditions(self, start_time=0, end_time=100, steps=10000):
    self.simulation_conditions.startTime = start_time
    self.simulation_conditions.endTime = end_time
    self.simulation_conditions.ninvertals = steps

  def run_simulation(self):
    if self.modelsource == "Biomodels":
      self.set_biomodels(self.model_inf)
      if self.error == 0:
        try:
          self.simulation_manager()
          self.basico2network()
        except Exception as e:
          print("Error in simulation: " + str(e))
          self.error = 1
    

  # simulation execution and results output
  def simulation_manager(self):

    self.simulation_results.species_values, self.simulation_results.reaction_values = self.simulation(start_time=self.simulation_conditions.startTime,
      end_time=self.simulation_conditions.endTime,
      steps=self.simulation_conditions.ninvertals,
      method=self.simulation_conditions.solver,
      atol=self.simulation_conditions.atol,
      rtol=self.simulation_conditions.rtol) 

    # print("Simulation done")


  # set information from basico data structure to this application (*)essential: sbml_id
  def set_biomodels(self, model_id): 
    # initial values, not edit these variables
    try:
      self.basico.model = load_biomodel(model_id)
    except Exception as e:
      print("Error in loading the model: " + model_id)
      print(e)
      self.error = 1
      return
    self.basico.species = get_species(model=self.basico.model)
    self.basico.reactions = get_reactions(model=self.basico.model)
    self.basico.functions = get_functions(model=self.basico.model)
    self.basico.parameters = get_parameters(model=self.basico.model)
    # self.basico.model_info = biomodels.get_model_info(model_id)
    if self.basico.reactions is None:
      print("No reactions found in the model: " + model_id)
      self.error = 1
    elif len(self.basico.reactions) == 0:
      print("No reactions found in the model: " + model_id)
      self.error = 1


  
  def set_edge(self, r, tcID, src, tar, type, label):
    if src == 'null' or src == 'Null' or src == 'NULL':
      src = "null_node"
    if tar == 'null' or tar == 'Null' or tar == 'NULL':
      tar = "null_node"

    self.network.edges.append({"tcID": tcID, "reactant":src.strip().replace('"', ''), "product":tar.strip().replace('"', ''), "type":type, "label":label})
    r += 1
    return r

  def basico2network(self):
    r = 0
    for i in range(len(self.basico.reactions)):
      rID = self.basico.reactions.index[i]
      scheme = self.basico.reactions['scheme'].iloc[i]
      function_name = self.basico.reactions['function'].iloc[i]
      ratelaw = self.basico.functions.loc[function_name,'formula']
      mapping = self.basico.reactions['mapping'].iloc[i]
      # if function_name == "Mass action (reversible)" or function_name == "Mass action (irreversible)":
      for key, values in mapping.items():
        # print(key, values, type(values))
        if type(values) == list:
          value = "*".join(values)
        elif type(values) == float or type(values) == int:
          value = str(values)
        else:
          value = values[0]
        if key == "substrate":
          ratelaw = ratelaw.replace("PRODUCT<substrate_i>", value)
        elif key == "product":
          ratelaw = ratelaw.replace("PRODUCT<product_j>", value)
        else:
          # print(key, value)
          value = value.replace("'", "prime")
          ratelaw = ratelaw.replace(key, value)
      tcID = "(" + rID + ").Flux"
    
      if ";" in scheme: #modification
        # print(scheme)
        scheme = scheme.split(";")
        reaction = scheme[0].strip()
        modifiers = scheme[1].strip()
      else:
        reaction = scheme
        modifiers = None

      if "=" in reaction or "->" in reaction:
        if "=" in reaction:
          reaction = reaction.split("=")
        elif "->" in reaction:
          reaction = reaction.split("->")
        reactants = reaction[0].strip()
        products = reaction[1].strip()
        if reactants == "":
          if len(products.split(" + ")) > 1:
            reactants = rID + "_src"
          else:
            reactant = products + "_src"
        else:
          reactant = reactants
        if products == "":
          if len(reactants.split(" + ")) > 1:
            products = rID + "_deg"
          else:
            product = reactants + "_deg"
        else:
          product = products

        if len(reactants.split(" + ")) > 1 or len(products.split(" + ")) > 1:
          binding = rID + "_mod"
          for reactant in reactants.split(" + "):
            r = self.set_edge(r, tcID, reactant, binding, "->", ratelaw)
          for product in products.split(" + "):
            r = self.set_edge(r, tcID, binding, product, "->", ratelaw)
          if modifiers is not None:
            # print("modifiers:", modifiers)
            modifiers = modifiers.replace("'", "prime")
            for modifier in shlex.split(modifiers):
              r = self.set_edge(r, modifier, modifier, binding, "-o", ratelaw)
        else:
          if modifiers is not None:
            r = self.set_edge(r, tcID, reactant, rID+"_mod", "->", ratelaw)
            r = self.set_edge(r, tcID, rID+"_mod", product, "->", ratelaw)
            modifiers = modifiers.replace("'", "prime")
            for modifier in shlex.split(modifiers):
              r = self.set_edge(r, modifier, modifier, rID+"_mod", "-o", ratelaw)
          else:
            r = self.set_edge(r, tcID, reactant, product, "->", ratelaw)
       

  # 
  def simulation(self, method="lsoda", start_time=0, end_time=100, steps = 10000, atol=1e-12, rtol=1e-6):

    output_columns = ['Time']
    name_flux = {}
    # print(self.basico.reactions)
    for key in self.basico.reactions['display_name']:
      name_flux[key] = key + ".Flux"
      output_columns.append(name_flux[key])
    name_parameter_var = {}
    # print(self.basico.parameters)
    for i in range(len(self.basico.parameters.index)):
      key = self.basico.parameters.index[i]
      type = self.basico.parameters['type'].iloc[i]
      if type == 'assignment' or type == 'ode':
        name_parameter_var[key] = self.basico.parameters['display_name'].iloc[i]
        output_columns.append(name_parameter_var[key])
    
    # print(name_flux)
    # print(name_parameter_var)
    
    if method == "lsoda":
      # time is included in the output, column names are key' names of species and reactions
      s_tc = run_time_course(model=self.basico.model, method=method, start_time=start_time, duration=end_time, intervals=steps, a_tol=atol, r_tol=rtol)
      flux_tc = run_time_course_with_output(model=self.basico.model, output_selection=output_columns, method=method, start_time=start_time, duration=end_time, intervals=steps, a_tol=atol, r_tol=rtol).set_index('Time')

    return s_tc, flux_tc
  

####################################################

if __name__ == "__main__":
  # timecourse_data, diagram_data = biomodels2dynet("BIOMD0000000001")
  timecourse_data, diagram_data = biomodels2dynet("BIOMD0000000007", start_time=0, end_time=10000, steps=10000)
  # print(timecourse_data)
  # print(diagram_data)