import tkinter
import tkinter.ttk as ttk
import tkinter.filedialog
from SBDyNetVis.make_dynet import MakeDyNet
import SBDyNetVis.biomodels2dynet as biomodels2dynet 
import pandas as pd
import json, os, sys
import importlib.resources
import threading

class SBDyNetVisGUI(tkinter.Tk):
    def __init__(self):
      super().__init__()

      self.title("SBDyNetVis")

      main_frame = tkinter.Frame(self)
      main_frame.grid_rowconfigure(0, weight=1)
      main_frame.grid_columnconfigure(0, weight=1)
      main_frame.pack(pady=10)

      # progress bar
      var = tkinter.IntVar()
      self.pb=ttk.Progressbar(main_frame,mode="indeterminate",variable=var)
      
      self.currentFrame = 0

      # Select modes
      label1 = tkinter.Label(main_frame, text='Select mode: ')
      label1.grid(row=0, column=0, padx=5, sticky=tkinter.E)

      # Combobox for selecting model type
      combo = ttk.Combobox(main_frame, values=["Your model", "biomodels"], state="readonly")
      combo.current(0)  # Default value
      combo.bind("<<ComboboxSelected>>", self.main_selected)
      combo.grid(row=0, column=1, sticky=tkinter.W, padx=5)

      # Input frame
      self.input_frame = tkinter.Frame(main_frame)
      self.input_frame.grid(row=1, column=1, columnspan=2, sticky="nsew")

      self.biomodels_frame = ttk.Frame(self.input_frame)
      self.biomodels_frame.grid(row=0, column=0, sticky="nsew", pady=20)
      self.firstselect_biomodels = False
      self.biomodels()

      self.original_model_frame = ttk.Frame(self.input_frame)
      self.original_model_frame.grid(row=0, column=0, sticky="nsew", pady=20)
      self.original_model()

      
    # Switch input frames
    def main_selected(self, event):
      selected_value = event.widget.get()
      if selected_value == "Your model":
          self.currentFrame = 0
          self.original_model_frame.tkraise()
      elif selected_value == "biomodels":
          if self.firstselect_biomodels == False:
            self.selected_biomodels(None)  # Set default selection
            self.firstselect_biomodels = True
          self.currentFrame = 1
          self.biomodels_frame.tkraise()
    
    # read json for pyinstaller
    def resource_path(self, relative_path):
      if hasattr(sys, '_MEIPASS'):
        base_path = sys._MEIPASS
      else:
        base_path = os.path.abspath(".")
      return os.path.join(base_path, relative_path)
    
    # Biomodels input frame
    def biomodels(self):
      # Select modes
      label1 = tkinter.Label(self.biomodels_frame, text='Select: ')
      label1.grid(row=0, column=0, padx=5, sticky=tkinter.E)

      # # directly execute python script
      # with open("confirmed_list_biomodels.json", "r", encoding="utf-8") as f:
      #   biomodels_list = json.load(f)
      # # GUI application
      # with open(self.resource_path("confirmed_list_biomodels.json"), "r", encoding="utf-8") as f: 
      #   biomodels_list = json.load(f)
      # read json from package
      with importlib.resources.open_text('SBDyNetVis', 'confirmed_list_biomodels.json', encoding='utf-8') as f:
        biomodels_list = json.load(f)
      biomodels_list = [f"{item['id']}: {item['name']}" for item in biomodels_list]

      self.model_inf = tkinter.StringVar()
      combo = ttk.Combobox(self.biomodels_frame, values=biomodels_list, textvariable=self.model_inf, state="readonly", width=27)
      combo.current(0)
      
      combo.bind("<<ComboboxSelected>>", self.selected_biomodels)
      combo.grid(row=0, column=1, padx=5)

      # Input start time
      label1 = tkinter.Label(self.biomodels_frame, text='Start time:')
      label1.grid(row=1, column=0, padx=5, sticky=tkinter.E)
      self.start_time = tkinter.Entry(self.biomodels_frame, justify=tkinter.RIGHT, width=30)
      self.start_time.insert(0, '0')  # Default value for start time
      self.start_time.grid(row=1, column=1, padx=5)
      # Input end time
      label2 = tkinter.Label(self.biomodels_frame, text='End time:')
      label2.grid(row=2, column=0, padx=5, sticky=tkinter.E)
      self.end_time = tkinter.Entry(self.biomodels_frame, justify=tkinter.RIGHT, width=30)
      self.end_time.insert(0, '100') # Default value for end time
      self.end_time.grid(row=2, column=1, padx=5)
      # Input steps
      label3 = tkinter.Label(self.biomodels_frame, text='Steps:')
      label3.grid(row=3, column=0, padx=5, sticky=tkinter.E)
      self.steps = tkinter.Entry(self.biomodels_frame, justify=tkinter.RIGHT, width=30)
      self.steps.insert(0, '1000') # Default value for steps
      self.steps.grid(row=3, column=1, padx=5)

      # Whether output code.js in local
      label4 = tkinter.Label(self.biomodels_frame, text='Output code.js in local:')
      label4.grid(row=4, column=0, padx=5, sticky=tkinter.E)
      self.var1 = tkinter.IntVar()
      check_button = tkinter.Checkbutton(self.biomodels_frame, text="Yes", variable=self.var1)
      check_button.grid(row=4, column=1, padx=5)

      # Run button
      run_button = tkinter.Button(
          self.biomodels_frame,
          text='Run',
          command=self.run
      )
      run_button.grid(row=5, column=1, sticky=tkinter.W)

      self.pb.grid(row=6, column=0)

    def selected_biomodels(self, event):
      selected = self.model_inf.get()
      model_id = selected.split(':')[0]
      print(f"Selected biomodel: {model_id}")
      self.model_inf_id = model_id
       

    # Original model input frame
    def original_model(self):

      # Input model name
      label1 = tkinter.Label(self.original_model_frame, text='Model/Output name:')
      label1.grid(row=0, column=0, padx=5, sticky=tkinter.E)
      self.modelName = tkinter.Entry(self.original_model_frame, width=30)
      self.modelName.grid(row=0, column=1, padx=5)

      # Input timecourse csv
      read_button = tkinter.Button(
          self.original_model_frame,
          text='Open timecourse csv',
          command=self.read_button_func
      )
      read_button.grid(row=1, column=0, padx=5, sticky=tkinter.E)
      self.tclabel = tkinter.Label(self.original_model_frame, text='')
      self.tclabel.grid(row=1, column=1, padx=5)

      # Input diag csv
      read_button2 = tkinter.Button(
          self.original_model_frame,
          text='Open diag csv',
          command=self.read_button_func2
      )
      read_button2.grid(row=2, column=0, padx=5, sticky=tkinter.E)
      self.diaglabel = tkinter.Label(self.original_model_frame, text='')
      self.diaglabel.grid(row=2, column=1, padx=5)

      # Whether output code.js in local
      label4 = tkinter.Label(self.original_model_frame, text='Output code.js in local:')
      label4.grid(row=3, column=0, padx=5, sticky=tkinter.E)
      self.var2 = tkinter.IntVar()
      check_button = tkinter.Checkbutton(self.original_model_frame, text="Yes", variable=self.var2)
      check_button.grid(row=3, column=1, padx=5)

      # Run button
      run_button = tkinter.Button(
          self.original_model_frame,
          text='Run',
          command=self.run
      )
      run_button.grid(row=4, column=1, sticky=tkinter.W)

      self.pb.grid(row=5, column=0)
      
    def file_read(self):
      file_path = tkinter.filedialog.askopenfilename()

      if len(file_path) != 0:
          data = pd.read_csv(file_path)
      else:
          data = ''

      return data, file_path
    
    def read_button_func(self):
      self.tcdata, self.tclabel['text'] = self.file_read()

    def read_button_func2(self):
      self.diagdata, self.diaglabel['text']  = self.file_read()


    def run(self):
      self.pb.start(interval=10)

      def task():
        
        if self.currentFrame == 0:
          # Original model
          if self.tcdata.empty or self.diagdata.empty:
              print("Please input timecourse and diag csv files.")
              return
          if self.modelName.get() == '':
            modelName = "result"
          else:
            modelName = self.modelName.get()
          localCode = self.var2.get()
          if localCode == 1:
            localCode = True
          else:
            localCode = False
          dynet = MakeDyNet(self.tcdata, self.diagdata,  
                              modelName=modelName,
                              localCode=localCode)
          dynet.run()

        elif self.currentFrame == 1:
          # Biomodels
          start_time = 0 if self.start_time.get() == '' else float(self.start_time.get())
          end_time = 0 if self.end_time.get() == '' else float(self.end_time.get())
          steps = 0 if self.steps.get() == '' else float(self.steps.get())
          localCode = self.var1.get()
          if localCode == 1:
            localCode = True
          else:
            localCode = False

          dynet = biomodels2dynet.biomodels2dynet(self.model_inf_id, 
                                                        start_time=start_time,
                                                        end_time=end_time,
                                                        steps=steps,
                                                        localCode=localCode)
        
        self.pb.stop()
      
      thread = threading.Thread(target=task)
      thread.start()



# GUI generation
# app = SBDyNetVisGUI()
# app.mainloop()
