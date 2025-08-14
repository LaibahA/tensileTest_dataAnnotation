import os, json

from rdflib import Graph, Namespace, Literal
#Graph stores the RDF triples, Namespace is what lets us define the prefixes
from rdflib.namespace import RDF, XSD
#RDF is for the standard datatypes

#Input and output directories
#input_dir = "../data/FAIRtrain_data_json"
input_dir = "../data/FAIRtrain_example"
output_dir_jsonld = "../output/annotatedBy_TTO/jsonld_output"
output_dir_ttl = "../output/annotatedBy_TTO/ttl_output"

#Loop through each JSON file in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith(".json"):
        filepath = os.path.join(input_dir, filename)

        g = Graph()  #Empty graph to store triples

        TTO = Namespace(
            "https://materialdigital.github.io/application-ontologies/tto/#/")  #Here we are just saying that TTO is the namespace for our ontology
        g.bind("tto", TTO)  #Binding namespace to prefix, makes it easier to use

        '''
        Need to update namespace below to our domain
        '''
        EX = Namespace("http://example.org/tensile/")  #This is an example, its gna be what builds the uri for our subject to annotate.
        g.bind("ex", EX)

        with open(filepath) as f:
            data = json.load(f) #Makes the list of rows

            #Make uris
            sample_id = data["sample_id"]
            test_uri = EX[sample_id]
            test_piece_id = sample_id.split("_")[2]
            test_piece_uri = EX["testPiece_" + test_piece_id]
            machine_uri = EX[data["sample_id"][:6]]

            #Declare test, test machine, and test piece
            g.add((test_uri, RDF.type, TTO.TensileTest))
            g.add((test_piece_uri, RDF.type, TTO.TestPiece))
            g.add((machine_uri, RDF.type, TTO.TensileTestingMachine))

            #Establish relationships between tensile test to test piece and machine
            # BFO_0000057, has participant
            g.add((test_uri, TTO.BFO_0000057, test_piece_uri))
            g.add((test_uri, TTO.BFO_0000057, machine_uri))

            #Original width
            #Creating a node to represent the concept of width for our data
            width_node = EX[f"width"]
            #Saying this node (subject) is a (predicate) object of this type (object)
            g.add((width_node, RDF.type, TTO.OriginalWidth))
            #Saying this node (subject) has numeric value (predicate) of this float (object)
            g.add((width_node, TTO.PMD_0000006, Literal(data["width"], datatype=XSD.float))) # PMD_0000006, has value
            g.add((width_node, TTO.PMD_0000020, Literal("mm"))) # PMD_0000020, has measurement unit label
            #Saying this node (subject) is a measurement relating to (predicate) the test piece (object)
            g.add((width_node, TTO.IAO_0000221, test_piece_uri)) # IAO_0000221, is quality measurement of

            #Original thickness
            thickness_node = EX[f"thickness"]
            g.add((thickness_node, RDF.type, TTO.OriginalThickness))
            g.add((thickness_node, TTO.PMD_0000006, Literal(data["thickness"], datatype=XSD.float)))
            g.add((thickness_node, TTO.PMD_0000020, Literal("mm")))
            g.add((thickness_node, TTO.IAO_0000221, test_piece_uri))

            #Gauge length
            length_node = EX[f"length"]
            g.add((length_node, RDF.type, TTO.OriginalGaugeLength))
            g.add((length_node, TTO.PMD_0000006, Literal(data["length"], datatype=XSD.float)))
            g.add((length_node, TTO.PMD_0000020, Literal("mm")))
            g.add((length_node, TTO.IAO_0000221, test_piece_uri))

            #Youngs modulus / slope of the elastic part
            youngs_mod_node = EX[f"youngs_modulus"]
            g.add((youngs_mod_node, RDF.type, TTO.SlopeOfTheElasticPart))
            g.add((youngs_mod_node, TTO.PMD_0000006, Literal(data["extracted_properties"]["youngs_modulus"], datatype=XSD.float)))
            g.add((youngs_mod_node, TTO.IAO_0000221, test_piece_uri))

            #Ultimate tensile strength / upper yield strength
            ult_tensile_strength = EX[f"ultimate_tensile_strength"]
            g.add((ult_tensile_strength, RDF.type, TTO.UpperYieldStrength))
            g.add((ult_tensile_strength, TTO.PMD_0000006, Literal(data["extracted_properties"]["ultimate_tensile_strength"], datatype=XSD.float)))
            g.add((ult_tensile_strength, TTO.IAO_0000221, test_piece_uri))

            for i, point in enumerate(data["data"]):
                #Force
                force_node = EX[f"pair_{i}_force"]
                g.add((force_node, RDF.type, TTO.Force))
                g.add((force_node, TTO.PMD_0000006, Literal(point["N"], datatype=XSD.float)))
                g.add((force_node, TTO.PMD_0000020, Literal("N")))
                g.add((force_node, TTO.IAO_0000221, test_piece_uri))

                #Elongation
                elong_node = EX[f"pair_{i}_elongation"]
                g.add((elong_node, RDF.type, TTO.Elongation))
                g.add((elong_node, TTO.PMD_0000006, Literal(point["mm"], datatype=XSD.float)))
                g.add((elong_node, TTO.PMD_0000020, Literal("mm")))
                g.add((elong_node, TTO.IAO_0000221, test_piece_uri))

                #Pairing the elongation and force
                g.add((force_node, TTO.BFO_0000195, elong_node)) # BFO_0000195, specifically depends on

            output_base_jsonld = os.path.join(output_dir_jsonld, f"annotated_{sample_id}")
            output_base_ttl = os.path.join(output_dir_ttl, f"annotated_{sample_id}")

            #Serializing in jsonld and ttl
            g.serialize(output_base_jsonld + ".jsonld", format="json-ld")
            g.serialize(output_base_ttl + ".ttl", format="turtle")