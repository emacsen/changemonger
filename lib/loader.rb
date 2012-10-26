require Changemonger::Features
module Changemonger::DB::Loader
  
  def feature(name, &block)
    obj = Feature.new(name)
    obj.instance_eval(&block)
    
  end
