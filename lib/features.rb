require 'ActiveSupport::Inflector::Inflections'

module Changemonger::Features

  class Feature
    # The base Feature type, unpon which other Features are built
    def initialize(name)
      @name = name
      @types = []
      @categories = []
      @prominence = 0
      @label = name
    end
    
    def category(cat)
      @categories.push(cat)
    end
    
    def match(element)
      nil
    end
    
    def precision
      0
    end
    
    def plural
      @name.pluralize
    end
    
    def type(value)
      if value == :node or value == :way or value == :relation
        @types.push value
        # WE NEED AN EXCEPTION IF THE TYPE DOESN'T MATCH
      end
    end
    
    def typecheck(element)
      @types.include?(element.type)
    end
    
  end
  
  class SimpleFeature < Feature
    def initialize(name)
      super(name)
      @tags = {}
    end
    
    def tag(value)
      @tags.push(value)
    end
    
    def tagmatch(element)
      @tags.all? { |tag| @element.tags.include? tag}
    end
    
    def match(element)
      if typecheck(element) and tagmatch(element) 
        Match(self, element)
      end
    end
    
  end
  
  class FeatureCategory < Feature
    def initialize(name)
      super(name)
      @features = []
      # By default, categories are precision 3
      @precision = 3
    end
    
    def register(feature)
      @features.push(feature)
    end
    
    def match(element)
      if @features.any? {|feature| feature.match(element) }
        Match(self, element)
      end
    end
  end
  
  class Match
    def initialize(feature, element)
      @feature = feature
      @element = element
      @tags = element.tags
    end
    
    def prominence
      # These prominence rules are hardcoded for now. We should change
      # this at some point.
      score = @feature.promince
      if @tags.length > 0:
          score = score + 1
      end
      if @tags.has_key "wikipedia"
        score = score + 3
      end
      if @tags.has_key "historic"
        score = score + 2
      end
      # We need a way to check for all OSM identifiers
      if @tags["name"] or @tags["operator"] or @tags["brand"] or @tags['ref']
        score = score + 2
      end
      # One day we need to check for object size (or at least # of nodes)
      return score
    end
    
    def specificity
      if @tags['name'] or @tags['operator'] or @tags['brand'] or @tags['ref']
        20
      else
        @feature.precision
      end
    end
    
    def label
      ### This should (mostly) be handled by the template filter)
      pass
    end
    
  end
  
  class MatchGroup
    
    def prominence
      @features.min{|a,b| a.prominence <=> b.prominence}.prominence
    end
    
    class FeatureDB
      def initialize
        @features = {}
      end
      
      def match_best(element)
        matches = @features.select{|f| f.match(element)}
        matches.sort! {|a,b| b.precision - a.precision}
        matches.shift
      end
      
      def match(element)
        matches = @features.select{|f| f.match(element)}
        matches.sort {|a,b| b.precision - a.precision}
      end
      
      def categories
        @features.select{|f| f.class.eql(FeatureCategory)}
      end
      
      def category(cat)
        if @features.has_key? cat.name
          raise IndexError, 'A feature named "%{cat.name}" already present in the database'
        elsif @features[cat.name].class != Category
          raise TypeError, 'Feature by the name "%{cat.name}" present in DB but not a Category'
        end
        @features.push(cat)
      end
      
      def match_all(element_array)
        element_array.collect {|e| e.match(e)}
      end  
    end
  end

end
