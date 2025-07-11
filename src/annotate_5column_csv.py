from rdflib import Graph, Namespace, Literal
# Graph stores the RDF triples, Namespace is what lets us define the prefixes, Literal is in case we have nums/strings
from rdflib.namespace import RDF, XSD
# RDF is for the standard datatypes, XSD is so the values we write serialize how we want. see usage for gauge length example
import csv

g = Graph() # Empty graph to store triples

TTO = Namespace("https://materialdigital.github.io/application-ontologies/tto/#/") # Here we are just saying that TTO is the namespace for our ontology
g.bind("tto", TTO) # Binding namespace to prefix, makes it easier to use

EX = Namespace("http://example.org/tensile/") # This is an example, its gna be what builds the uri for our subject to annotate
g.bind("ex", EX)

with open("../data/example_5column.csv") as f:
    reader = csv.DictReader(f) # Gives each line as a dict where the column header corresponds to the contents
    for row in reader:
        test_uri = EX[row["TestID"]] # test_uri is the uri for the test, eg. http://example.org/tensile/T1 - This gives subject of the triple

        g.add((test_uri, RDF.type, TTO.TensileTest)) # This creates a triple, eg: T1 is a TensileTest
        # It says: test_uri (subject), is a (RDF.type is the predicate), tensile test (TensileTest from TTO is the object).

        g.add((test_uri, TTO.hasTestingMachine, Literal(row["Machine"]))) # eg: T1 has testing machine MachineA
        # It says: test_uri (subject), has a testing machine (predicate), specified machine (object)

        g.add((test_uri, TTO.hasTestPiece, Literal(row["TestPiece"]))) # eg: T1 has test piece specimenA
        # It says: test_uri (subject), has a test piece (predicate), specified test piece (object)

        # g.add((test_uri, TTO.hasGaugeLength, Literal(float(row["GaugeLength"]))))  This prints with scientific notation. See below for using XSD
        g.add((test_uri, TTO.hasGaugeLength, Literal(row["GaugeLength"], datatype=XSD.integer))) # eg: T1 has test gauge length 50
        # It says: test_uri (subject), has a gauge length (predicate), specified gauge length (object)

        test_piece_uri = EX[row["TestPiece"]] # Now we are annotating the test piece, and saying it has thickness, so lets make this uri
        g.add((test_piece_uri, TTO.hasThickness, Literal(row["OriginalThickness"], datatype=XSD.integer))) # eg: T1 has original thickness 3
        # It says: test_piece_uri (subject), has a thickness (predicate), specified original thickness (object)

g.serialize("../output/5column/csv_input_turtle_output.ttl", format="turtle")
g.serialize("../output/5column/csv_input_jsonld_output.jsonld", format="json-ld")





