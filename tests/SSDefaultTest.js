// ==Builder==
// @test
// @name        SSDefaultTest
// @suite       SSDefaultTestSuite
// ==/Builder==

function TestCaseDivide(x, y)
{
  if(y == 0) throw new TestCaseTestDivideByZeroException(new Error());
}

var SSDefaultTest = new Class({
  
  name: 'SSTestCaseTest',

  Extends: SSUnitTest.TestCase,

  testAdd: function()
  {
    this.assertEqual(2+3, 5);
  },

  testDivide: function()
  {
    this.assertThrows(TestCaseTestDivideByZeroException, TestCaseDivide, 5, 0);
  },

  testSubstract: function()
  {
    var x = 5;
    this.assertNotEqual(x-2, 5);
  },

  testShouldFail: function()
  {
    var x = 5;
    this.assertNotEqual(x, 5);
  },

  testMultiply: function()
  {
    this.assert((3*3) == 9);
  }
    
});