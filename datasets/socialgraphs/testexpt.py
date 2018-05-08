import unittest
import demo
from os import listdir
from os.path import isfile, join
from matplotlib import pyplot

class TestAccTF(unittest.TestCase):

  # def testCiteseer(self):
  #   init_acc,final_acc = demo.runMain("--stem citeseer".split())
  #   self.assertTrue( 0.62 <= init_acc < final_acc < 0.65 )

  # def testCora(self):
  #   init_acc,final_acc = demo.runMain("--stem cora".split())
  #   self.assertTrue( 0.75 <= init_acc < final_acc < 0.80 )

  # def testDolphins(self):
  #   init_acc,final_acc = demo.runMain("--stem dolphins".split())
  #   self.assertTrue( init_acc == final_acc == 1.0 )

  # def testFootball(self):
  #   init_acc,final_acc = demo.runMain("--stem football --regularizer_scale 1.0".split())
  #   self.assertTrue( 0.43 < init_acc < 0.45 )
  #   self.assertTrue( 0.70 < final_acc < 0.75 )

  # def testKarate(self):
  #   init_acc,final_acc = demo.runMain("--stem karate".split())
  #   self.assertTrue( 0.90 < init_acc < 1.0 )
  #   self.assertTrue( 0.90 < final_acc < 1.0 )

  # def testUMBC(self):
  #   init_acc,final_acc = demo.runMain("--stem umbc --link_scale 0.1".split())
  #   self.assertTrue( 0.94 < init_acc < final_acc < 0.95)

  # def testTwitter(self):
  #   init_acc,final_acc = demo.runMain("--stem Twitter --link_scale 0.1".split())
  #   self.assertTrue( 0.94 < init_acc < final_acc < 0.95)

  # def testTwitterEchoChamber(self):
  #   init_acc,final_acc = demo.runMain("--stem EchoChamber --link_scale 0.1".split())
  #   self.assertTrue( 0.94 < init_acc < final_acc < 0.95)

  
  def testSyntheticPlantedPartition(self):

      def isclose(a, b, rel_tol=1e-09, abs_tol=0.0):
          return abs(a-b) <= max(rel_tol * max(abs(a), abs(b)), abs_tol)


      files_path = './inputs'
      onlyfiles = [f for f in listdir(files_path) if isfile(join(files_path, f))]

      # def MySortFn(s):
      #   return int(s.split('_')[4]) - int(s.split('_')[5])

      sorted(onlyfiles) #, key=MySortFn

      for prob in range(5, 10, 1):
        attribute_match_prob = 0.1 * prob

        initial_accuracies = []
        final_accuracies = []
        c_ins = []
        c_outs = []
        c_in_minus_c_outs = []
        n =0


        #planted_partition_with_attributes_11.0_5.0.cfacts
        for facts_file in onlyfiles:
          if 'planted_partition_with_attributes_1000' in facts_file and 'cfacts' in facts_file:
            

            # planted_partition_with_attributes_11.0_5.0.cfacts

            file_name = facts_file.split('.cfacts')[0]

            file_prob = float(file_name.split('_')[-1])

            if isclose(file_prob, attribute_match_prob):
              print(facts_file)
              n = int(file_name.split('_')[4])
              c_in = float(file_name.split('_')[6])
              c_out = float(file_name.split('_')[7])
              # planted_partition_with_attributes_12.0_4.0
              init_acc,final_acc = demo.runMain(("--stem "+file_name).split())

              initial_accuracies.append(init_acc)
              final_accuracies.append(final_acc)

              c_ins.append(c_in)
              c_outs.append(c_out)
              c_in_minus_c_outs.append(c_in-c_out )


            # self.assertTrue( 0.60 < init_acc < 1.0 )
            # self.assertTrue( 0.80 < final_acc < 1.0 )
        print('c_ins', c_ins)
        print('c_outs', c_outs) 
        print('c_in_minus_c_outs' , c_in_minus_c_outs)   
        print('initial_accuracies' , initial_accuracies)
        print('final_accuracies' , final_accuracies)

        pyplot.plot(c_in_minus_c_outs, initial_accuracies, 'g-', \
          c_in_minus_c_outs, final_accuracies, 'r-')

        pyplot.savefig('results_plot_' +str(n)+ '_' + str(attribute_match_prob) + '_.png')



if __name__ == "__main__":
  unittest.main()
