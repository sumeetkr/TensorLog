import unittest
import sys
import theano
import os
import numpy as np

from tensorlog import declare
from tensorlog import matrixdb
from tensorlog import mutil
from tensorlog import parser
from tensorlog import program
from tensorlog import testtensorlog
from tensorlog import theanoxcomp
from tensorlog import tensorflowxcomp


TESTED_COMPILERS = [
  theanoxcomp.DenseMatDenseMsgCrossCompiler,
  theanoxcomp.SparseMatDenseMsgCrossCompiler,
  tensorflowxcomp.DenseMatDenseMsgCrossCompiler,
  tensorflowxcomp.SparseMatDenseMsgCrossCompiler,
]

class TestXCSmallProofs(testtensorlog.TestSmallProofs):

  def test_if(self):
    self.xcomp_check(['p(X,Y):-spouse(X,Y).'], 'p(i,o)', 'william', {'susan':1.0})

  def test_failure(self):
    self.xcomp_check(['p(X,Y):-spouse(X,Y).'], 'p(i,o)', 'lottie', {matrixdb.NULL_ENTITY_NAME:1.0})

  def test_reverse_if(self):
    self.xcomp_check(['p(X,Y):-sister(Y,X).'], 'p(i,o)', 'rachel', {'william':1.0})

  def test_or(self):
    self.xcomp_check(['p(X,Y):-spouse(X,Y).', 'p(X,Y):-sister(X,Y).'], 'p(i,o)', 'william',
            {'susan':1.0, 'rachel':1.0, 'lottie':1.0, 'sarah':1.0})

  def test_chain(self):
    self.xcomp_check(['p(X,Z):-spouse(X,Y),sister(Y,Z).'], 'p(i,o)', 'susan',
            {'rachel':1.0, 'lottie':1.0, 'sarah':1.0})
    self.xcomp_check(['p(X,Z):-sister(X,Y),child(Y,Z).'], 'p(i,o)', 'william',
            {'charlotte':1.0, 'lucas':1.0, 'poppy':1.0, 'caroline':1.0, 'elizabeth':1.0})

  def test_mid(self):
    self.xcomp_check(['p(X,Y):-sister(X,Y),child(Y,Z).'], 'p(i,o)', 'william',
            {'sarah': 1.0, 'rachel': 2.0, 'lottie': 2.0})

  def test_nest(self):
    self.xcomp_check(['s(X,Y):-spouse(X,Y).','t(X,Z):-spouse(X,Y),s(Y,Z).'], 't(i,o)', 'susan', {'susan': 1.0})

  def test_back1(self):
    # fails for tensorflowxcomp
    self.xcomp_check(['p(X,Y):-spouse(X,Y),sister(X,Z).'], 'p(i,o)', 'william', {'susan': 3.0})

  def test_back2(self):
    self.xcomp_check(['p(X,Y):-spouse(X,Y),sister(X,Z1),sister(X,Z2).'],'p(i,o)','william',{'susan': 9.0})

  def test_rec1(self):
    program.DEFAULT_MAXDEPTH=4
    self.xcomp_check(['p(X,Y):-spouse(X,Y).','p(X,Y):-p(Y,X).'], 'p(i,o)','william',{'susan': 5.0})
    program.DEFAULT_MAXDEPTH=10
    self.xcomp_check(['p(X,Y):-spouse(X,Y).','p(X,Y):-p(Y,X).'], 'p(i,o)','william',{'susan': 11.0})

  def test_const_output(self):
    self.xcomp_check(['sis(X,W):-assign(W,william),child(X,Y).'], 'sis(i,o)', 'sarah', {'william': 1.0})
    self.xcomp_check(['sis(X,W):-assign(W,william),child(X,Y).'], 'sis(i,o)', 'lottie', {'william': 2.0})

  def test_const_chain1(self):
    self.xcomp_check(['p(X,S) :- assign(S,susan),sister(X,Y),child(Y,Z).'],'p(i,o)','william',{'susan': 5.0})

  def test_const_chain2(self):
    self.xcomp_check(['p(X,Pos) :- assign(Pos,pos),child(X,Y),young(Y).'],'p(i,o)','sarah',{'pos':1.0})
    self.xcomp_check(['p(X,Pos) :- assign(Pos,pos),child(X,Y),young(Y).'],'p(i,o)','lottie',{'pos':2.0})

  def test_alt_chain(self):
    self.xcomp_check(['p(X,W) :- spouse(X,W),sister(X,Y),child(Y,Z).'],'p(i,o)','william',{'susan': 5.0})
    pass

  def test_proppr1(self):
    w = 7*self.db.onehot('r1')+3*self.db.onehot('r2')
    self.proppr_xcomp_check(w,['p(X,Y):-sister(X,Y) {r1}.','p(X,Y):-spouse(X,Y) {r2}.'],'p(i,o)',
                'william', {'sarah': 7.0, 'rachel': 7.0, 'lottie': 7.0, 'susan': 3.0})

  def test_proppr2(self):
    w = 3*self.db.onehot('r2')
    self.proppr_xcomp_check(w,['p(X,Y):-spouse(Y,X) {r2}.'],'p(i,o)',
                'susan', {'william': 3.0})

  def test_reuse1(self):
    self.xcomp_check(['p(X,Y) :- r(X,Z),r(Z,Y).', 'r(X,Y):-spouse(X,Y).'], 'p(i,o)', 'william',
            {'william':1.0})


  def xcomp_check(self,ruleStrings,mode_string,input_symbol,expected_result_dict):
    self._xcomp_check('vanilla',None,ruleStrings,mode_string,input_symbol,expected_result_dict)

  def proppr_xcomp_check(self,weightVec,ruleStrings,mode_string,input_symbol,expected_result_dict):
    self._xcomp_check('proppr',weightVec,ruleStrings,mode_string,input_symbol,expected_result_dict)

  def _xcomp_check(self,progType,weightVec,ruleStrings,mode_string,input_symbol,expected_result_dict):
    # run the base class check to see that the inference is correct
    if progType=='proppr':
      self.proppr_inference_check(weightVec,ruleStrings,mode_string,input_symbol,expected_result_dict)
    else:
      self.inference_check(ruleStrings,mode_string,input_symbol,expected_result_dict)
    # setup the next round of tests by compiling a tensorlog
    # Program - this code is lifted from the testtensorlog
    # inference routines
    print 'xcomp inference for mode',mode_string,'on input',input_symbol
    testtensorlog.softmax_normalize(expected_result_dict)
    rules = parser.RuleCollection()
    for r in ruleStrings:
      rules.add(parser.Parser.parseRule(r))
    if progType=='proppr':
      prog = program.ProPPRProgram(db=self.db,rules=rules,weights=weightVec)
    else:
      prog = program.Program(db=self.db,rules=rules)
    mode = declare.ModeDeclaration(mode_string)
    tlogFun = prog.compile(mode)
    for compilerClass in TESTED_COMPILERS:
      #cross-compile the function
      xc = compilerClass(prog.db)
      xc.compile(tlogFun)
      # evaluate the function and get the output y
      xc.show()
      print '== performing eval with',compilerClass,'=='
      ys = xc.eval([prog.db.onehot(input_symbol)])
      y = ys[0]
      # theano output will a be (probably dense) message, so
      # just compare that maximal elements from these two dicts
      # are the same
      self.check_maxes_in_dicts(self.db.rowAsSymbolDict(y), expected_result_dict)
      print '== eval checks passed =='

  def check_maxes_in_dicts(self,actual,expected):
    def maximalElements(d):
      m = max(d.values())
      return set(k for k in d if d[k]==m)
    actualMaxes = maximalElements(actual)
    expectedMaxes = maximalElements(expected)
    print 'actual',actualMaxes,'expected',expectedMaxes
    for a in actualMaxes:
      self.assertTrue(a in expectedMaxes)
    for a in expectedMaxes:
      self.assertTrue(a in actualMaxes)


class TestXCGrad(testtensorlog.TestGrad):

  def setUp(self):
    self.db = matrixdb.MatrixDB.loadFile(os.path.join(testtensorlog.TEST_DATA_DIR,'fam.cfacts'))

  def test_if(self):
    rules = ['p(X,Y):-sister(X,Y).']
    mode = 'p(i,o)'
    params = [('sister',2)]
    self.xgrad_check(rules, mode, params,
                     [('william',['rachel','sarah'])],
                     {'sister(william,rachel)': +1,'sister(william,sarah)': +1,'sister(william,lottie)': -1})
    self.xgrad_check(rules, mode, params,
                     [('william',['lottie'])],
                     {'sister(william,rachel)': -1,'sister(william,lottie)': +1})

  def test_if2(self):
    rules = ['p(X,Y):-sister(X,Y).']
    mode = 'p(i,o)'
    params = [('sister',2)]
    self.xgrad_check(rules, mode, params,
                     [('william',['rachel','sarah']), ('william',['rachel','sarah'])],
                     {'sister(william,rachel)': +1,'sister(william,sarah)': +1,'sister(william,lottie)': -1})
    self.xgrad_check(rules, mode, params,
                     [('william',['lottie']), ('william',['lottie'])],
                     {'sister(william,rachel)': -1,'sister(william,lottie)': +1})

  def test_reverse_if(self):
    rules = ['p(X,Y):-parent(Y,X).']
    mode = 'p(i,o)'
    params = [('parent',2)]
    self.xgrad_check(rules, mode, params,
                     [('lottie',['charlotte'])],
                     {'parent(charlotte,lottie)': +1,'parent(lucas,lottie)': -1})

  def test_chain1(self):
    rules = ['p(X,Z):-sister(X,Y),child(Y,Z).']
    mode = 'p(i,o)'
    self.xgrad_check(rules,mode,
                     [('sister',2)],
                     [('william',['caroline','elizabeth'])],
                     {'sister(william,rachel)': +1,'sister(william,lottie)': -1})
    self.xgrad_check(rules,mode,
                     [('child',2)],
                     [('william',['caroline','elizabeth'])],
                     {'child(rachel,elizabeth)': +1,'child(lottie,lucas)': -1})
    self.xgrad_check(rules,mode,
                     [('child',2),('sister',2)],
                     [('william',['caroline','elizabeth'])],
                     {'child(rachel,elizabeth)': +1,'child(lottie,lucas)': -1, 'sister(william,rachel)': +1,'sister(william,lottie)': -1})

  def test_chain2(self):
    rules =  ['p(X,Z):-spouse(X,Y),sister(Y,Z).']
    mode = 'p(i,o)'
    self.xgrad_check(rules,mode,
                     [('sister',2)],
                     [('susan',['rachel'])],
                     {'sister(william,rachel)': +1,'sister(william,lottie)': -1})


  def test_call1(self):
    rules = ['q(X,Y):-sister(X,Y).','p(Z,W):-q(Z,W).']
    mode = 'p(i,o)'
    params = [('sister',2)]
    self.xgrad_check(rules, mode, params,
                     [('william',['rachel','sarah'])],
                     {'sister(william,rachel)': +1,'sister(william,sarah)': +1,'sister(william,lottie)': -1})
    self.xgrad_check(rules, mode, params,
                     [('william',['lottie'])],
                     {'sister(william,rachel)': -1,'sister(william,lottie)': +1})

  def test_call2(self):
    rules = ['q(X,Y):-sister(X,Y).','p(Z,W):-r(Z,W).','r(Z,W):-q(Z,W).']
    mode = 'p(i,o)'
    params = [('sister',2)]
    self.xgrad_check(rules, mode, params,
                     [('william',['rachel','sarah'])],
                     {'sister(william,rachel)': +1,'sister(william,sarah)': +1,'sister(william,lottie)': -1})
    self.xgrad_check(rules, mode, params,
                     [('william',['lottie'])],
                     {'sister(william,rachel)': -1,'sister(william,lottie)': +1})

  def test_split(self):
    rules = ['p(X,Y):-sister(X,Y),child(Y,Z),young(Z).']
    mode = 'p(i,o)'
    params = [('child',2)]
    self.xgrad_check(rules, mode, params,
                     [('william',['lottie'])],
                     {'child(lottie,lucas)': +1,'child(lottie,charlotte)': +1,'child(sarah,poppy)': -1})
    params = [('sister',2)]
    self.xgrad_check(rules, mode, params,
                     [('william',['lottie'])],
                     {'sister(william,lottie)': +1,'sister(william,sarah)': -1})

  def test_or(self):
    rules = ['p(X,Y):-child(X,Y).', 'p(X,Y):-sister(X,Y).']
    mode = 'p(i,o)'
    params = [('sister',2)]
    self.xgrad_check(rules, mode, params,
                     [('william',['charlie','rachel'])],
                     {'sister(william,rachel)': +1,'sister(william,sarah)': -1,'sister(william,lottie)': -1})
    params = [('child',2)]
    self.xgrad_check(rules, mode, params,
                     [('william',['charlie','rachel'])],
                     {'child(william,charlie)': +1,'child(william,josh)': -1})
    params = [('child',2),('sister',2)]
    self.xgrad_check(rules, mode, params,
                     [('william',['charlie','rachel'])],
                     {'child(william,charlie)': +1,'child(william,josh)': -1,'sister(william,rachel)': +1,'sister(william,sarah)': -1})


  def test_weighted_vec(self):
    rules = ['p(X,Y):-sister(X,Y),assign(R,r1),feat(R).','p(X,Y):-child(X,Y),assign(R,r2),feat(R).']
    mode = 'p(i,o)'
    params = [('sister',2)]
    self.xgrad_check(rules, mode, params,
                     [('william',['rachel','charlie'])],
                     {'sister(william,rachel)': +1,'sister(william,sarah)': -1})
    params = [('child',2)]
    self.xgrad_check(rules, mode, params,
                     [('william',['rachel','charlie'])],
                     {'child(william,charlie)': +1,'child(william,josh)': -1})
    params = [('feat',1)]
    self.xgrad_check(rules, mode, params,
                     [('william',['josh','charlie'])],
                     {'feat(r1)': -1,'feat(r2)': +1})
    self.xgrad_check(rules, mode, params,
                     [('william',['rachel','sarah','lottie'])],
                     {'feat(r1)': +1,'feat(r2)': -1})

  def xgrad_check(self,rule_strings,mode_string,params,xyPairs,expected):
    rules = testtensorlog.rules_from_strings(rule_strings)
    prog = program.Program(db=self.db,rules=rules)
    mode = declare.ModeDeclaration(mode_string)
    tlogFun = prog.compile(mode)
    # TODO: not working yet for mini-batches so check each example
    # individually
    for x,ys in xyPairs:
      data = testtensorlog.DataBuffer(self.db)
      data.add_data_symbols(x,ys)
      for compilerClass in TESTED_COMPILERS:
        xc = compilerClass(prog.db)
        xc.compile(tlogFun,params)
        result = xc.eval([data.get_x()])
        loss = xc.evalDataLoss([data.get_x()],data.get_y())
        updates = xc.evalDataLossGrad([data.get_x()],data.get_y())
        updates_with_string_keys = {}
        for (functor,arity),up in zip(params,updates):
          upDict = prog.db.matrixAsPredicateFacts(functor,arity,up)
          for fact,grad_of_fact in upDict.items():
            updates_with_string_keys[str(fact)] = grad_of_fact
        self.check_directions(updates_with_string_keys,expected)

class TestXCProPPR(testtensorlog.TestProPPR):
  
  def setUp(self):
    super(TestXCProPPR,self).setUp()
    self.tlogFun = self.prog.compile(self.mode)

  def evalxc(self,xc,input):
    rawPred = xc.eval([input])
    # trim small numbers to zero
    pred = mutil.mapData(lambda d:np.clip((d - 1e-5),0.00,9999.99), rawPred)
    pred.eliminate_zeros()
    return pred

  def testNativeRow(self):
    for compilerClass in [tensorflowxcomp.DenseMatDenseMsgCrossCompiler,
                          tensorflowxcomp.SparseMatDenseMsgCrossCompiler]:
      xc = compilerClass(self.prog.db)
      xc.compile(self.tlogFun)
      for i in range(self.numExamples):
        pred = self.evalxc(xc, self.X.getrow(i))
        d = self.prog.db.rowAsSymbolDict(pred)
        uniform = {'pos':0.5,'neg':0.5}
        self.check_dicts(d,uniform)

  def testNativeMatrix(self):

    for compilerClass in [tensorflowxcomp.DenseMatDenseMsgCrossCompiler,
                          tensorflowxcomp.SparseMatDenseMsgCrossCompiler]:
      xc = compilerClass(self.prog.db)
      xc.compile(self.tlogFun)
      pred = self.prog.eval(self.mode,[self.X])
      d0 = self.prog.db.matrixAsSymbolDict(pred)
      for i,d in d0.items():
        uniform = {'pos':0.5,'neg':0.5,}
        self.check_dicts(d,uniform)

  def testGradMatrix(self):
    pass
#  def testGradMatrix(self):
#    data = DataBuffer(self.prog.db)
#    X,Y = self.labeledData.matrixAsTrainingData('train',2)
#    learner = learn.OnePredFixedRateGDLearner(self.prog)
#    updates =  learner.crossEntropyGrad(declare.ModeDeclaration('predict(i,o)'),X,Y)
#    w = updates[('weighted',1)]
#    def checkGrad(i,x,psign,nsign):
#      ri = w.getrow(i)
#      di = self.prog.db.rowAsSymbolDict(ri)
#      for toki in self.rawData[x].split():
#        posToki = toki+'_pos'
#        negToki = toki+'_neg'
#        self.assertTrue(posToki in di)
#        self.assertTrue(negToki in di)
#        self.assertTrue(di[posToki]*psign > 0)
#        self.assertTrue(di[negToki]*nsign > 0)
#    for i,x in enumerate(self.rawPos):
#      checkGrad(i,x,+1,-1)
#    for i,x in enumerate(self.rawNeg):
#      checkGrad(i+len(self.rawPos),x,-1,+1)
#
#  def testLabeledData(self):
#    self.assertTrue(self.labeledData.inDB('train',2))
#    self.assertTrue(self.labeledData.inDB('test',2))
#    self.assertFalse(self.prog.db.inDB('train',2))
#    self.assertFalse(self.prog.db.inDB('test',2))
#
  def testMultiLearn1(self):
    pass
#  def testMultiLearn1(self):
#    mode = declare.ModeDeclaration('predict(i,o)')
#    dset = dataset.Dataset.loadExamples(
#        self.prog.db,
#        os.path.join(TEST_DATA_DIR,"toytrain.examples"),
#        proppr=True)
#    for mode in dset.modesToLearn():
#      X = dset.getX(mode)
#      Y = dset.getY(mode)
#      print mode
#      print "\tX "+mutil.pprintSummary(X)
#      print "\tY "+mutil.pprintSummary(Y)
#
#    learner = learn.FixedRateGDLearner(self.prog,epochs=5)
#    P0 = learner.datasetPredict(dset)
#    acc0 = learner.datasetAccuracy(dset,P0)
#    xent0 = learner.datasetCrossEntropy(dset,P0)
#    print 'toy train: acc0',acc0,'xent1',xent0
#
#    learner.train(dset)
#
#    P1 = learner.datasetPredict(dset)
#    acc1 = learner.datasetAccuracy(dset,P1)
#    xent1 = learner.datasetCrossEntropy(dset,P1)
#    print 'toy train: acc1',acc1,'xent1',xent1
#
#    self.assertTrue(acc0<acc1)
#    self.assertTrue(xent0>xent1)
#    self.assertTrue(acc1==1)
#
#    Udset = dataset.Dataset.loadExamples(
#        self.prog.db,
#        os.path.join(TEST_DATA_DIR,"toytest.examples"),
#        proppr=True)
#
#    P2 = learner.datasetPredict(Udset)
#    acc2 = learner.datasetAccuracy(Udset,P2)
#    xent2 = learner.datasetCrossEntropy(Udset,P2)
#    print 'toy test: acc2',acc2,'xent2',xent2
#
#    self.assertTrue(acc2==1)
#    ##
#
#
  def testLearn(self):
    pass
#  def testLearn(self):
#    mode = declare.ModeDeclaration('predict(i,o)')
#    X,Y = self.labeledData.matrixAsTrainingData('train',2)
#    learner = learn.OnePredFixedRateGDLearner(self.prog,epochs=5)
#    P0 = learner.predict(mode,X)
#    acc0 = learner.accuracy(Y,P0)
#    xent0 = learner.crossEntropy(Y,P0,perExample=True)
#
#    learner.train(mode,X,Y)
#    P1 = learner.predict(mode,X)
#    acc1 = learner.accuracy(Y,P1)
#    xent1 = learner.crossEntropy(Y,P1,perExample=True)
#
#    self.assertTrue(acc0<acc1)
#    self.assertTrue(xent0>xent1)
#    self.assertTrue(acc1==1)
#    print 'toy train: acc1',acc1,'xent1',xent1
#
#    TX,TY = self.labeledData.matrixAsTrainingData('test',2)
#    P2 = learner.predict(mode,TX)
#    acc2 = learner.accuracy(TY,P2)
#    xent2 = learner.crossEntropy(TY,P2,perExample=True)
#    print 'toy test: acc2',acc2,'xent2',xent2
#    self.assertTrue(acc2==1)
#

if __name__ == "__main__":
  unittest.main()
