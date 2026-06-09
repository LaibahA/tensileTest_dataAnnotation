import os, json

from rdflib import Graph, Namespace, Literal
#Graph stores the RDF triples, Namespace is what lets us define the prefixes
from rdflib.namespace import RDF, XSD
#RDF is for the standard datatypes

#Input and output directories
input_dir = "../data/FAIRtrain_data_json"
#input_dir = "../data/FAIRtrain_example"
output_dir_jsonld = "../output/annotatedBy_newOntology/jsonld_output"
output_dir_ttl = "../output/annotatedBy_newOntology/ttl_output"

#Loop through each JSON file in the input directory
for filename in os.listdir(input_dir):
    if filename.endswith(".json"):
        filepath = os.path.join(input_dir, filename)

        g = Graph()  #Empty graph to store triples

        NTTO = Namespace( #Using the new tensile testing ontology created by our team - lets prefix it as NTTO
            "https://webprotege.stanford.edu/#projects/bbc9ebd0-8a7b-49f3-aedf-36cb71ee8a37/edit/Classes/")  #Here we are just saying that NTTO is the namespace for our ontology
        g.bind("ntto", NTTO)  #Binding namespace to prefix, makes it easier to use

        '''
        Need to update namespace below to our domain
        '''
        EX = Namespace("http://example.org/tensile/")  #This is an example, its gna be what builds the uri for our subject to annotate.
        g.bind("ex", EX)

        with open(filepath) as f:
            data = json.load(f) #Makes the list of rows

            #Make uris
            sample_id = data["sample_id"]
            test_piece_id = sample_id.split("_")[2]
            test_piece = EX["testPiece_" + test_piece_id]
            machine = EX[data["sample_id"][:6]]

            #Declare test machine, and test piece
            g.add((test_piece, RDF.type, NTTO.Sample))
            g.add((machine, RDF.type, NTTO.Machine))

            #Original width
            #Creating a node to represent the concept of width for our data
            width_node = EX[f"{sample_id}_width"]
            #Saying this node (subject) is a (predicate) object of this type (object)
            g.add((width_node, RDF.type, NTTO.OriginalWidth))
            #Saying this node (subject) has value (predicate) of this float (object)
            g.add((width_node, NTTO.hasValue, Literal(data["width"], datatype=XSD.float)))
            #Saying this node (subject) has unit label (predicate) of this label type (object)
            g.add((width_node, NTTO.hasUnitLabel, Literal("mm")))
            #Saying the test piece (subject) has width (predicate) from details in width_node (object)
            g.add((test_piece, NTTO.hasWidth, width_node))

            #Original thickness
            thickness_node = EX[f"{sample_id}_thickness"]
            g.add((thickness_node, RDF.type, NTTO.OriginalThickness))
            g.add((thickness_node, NTTO.hasValue, Literal(data["thickness"], datatype=XSD.float)))
            g.add((thickness_node, NTTO.hasUnitLabel, Literal("mm")))
            g.add((test_piece, NTTO.hasThickness, thickness_node))

            #Gauge length
            length_node = EX[f"{sample_id}_length"]
            g.add((length_node, RDF.type, NTTO.OriginalGaugeLength))
            g.add((length_node, NTTO.hasValue, Literal(data["length"], datatype=XSD.float)))
            g.add((length_node, NTTO.hasUnitLabel, Literal("mm")))
            g.add((test_piece, NTTO.hasLength, length_node))

            #Youngs modulus / slope of the elastic part
            youngs_mod_node = EX[f"{sample_id}_youngs_modulus"]
            g.add((youngs_mod_node, RDF.type, NTTO.SlopeOfTheElasticPart))
            g.add((youngs_mod_node, NTTO.hasValue, Literal(data["extracted_properties"]["youngs_modulus"], datatype=XSD.float)))
            g.add((test_piece, NTTO.hasYoungsModulus, youngs_mod_node))

            #Ultimate tensile strength / upper yield strength
            ult_tensile_strength_node = EX[f"{sample_id}_ultimate_tensile_strength"]
            g.add((ult_tensile_strength_node, RDF.type, NTTO.UpperYieldStrength))
            g.add((ult_tensile_strength_node, NTTO.hasValue, Literal(data["extracted_properties"]["ultimate_tensile_strength"], datatype=XSD.float)))
            g.add((test_piece, NTTO.hasUTS, ult_tensile_strength_node))

            for i, point in enumerate(data["data"]):
                measured_data_node = EX[f"{sample_id}_measured_data_{i}"]
                g.add((measured_data_node, RDF.type, NTTO.MeasuredData))
                #Force
                force_node = EX[f"{sample_id}_force_{i}"]
                g.add((force_node, RDF.type, NTTO.Force))
                g.add((force_node, NTTO.hasValue, Literal(point["N"], datatype=XSD.float)))
                g.add((force_node, NTTO.hasUnitLabel, Literal("N")))
                g.add((measured_data_node, NTTO.hasForce, force_node))

                #Elongation
                elong_node = EX[f"{sample_id}_elongation_{i}"]
                g.add((elong_node, RDF.type, NTTO.Elongation))
                g.add((elong_node, NTTO.hasValue, Literal(point["mm"], datatype=XSD.float)))
                g.add((elong_node, NTTO.hasUnitLabel, Literal("mm")))
                g.add((measured_data_node, NTTO.hasElongation, elong_node))

                #Link data points to test piece
                g.add((test_piece, NTTO.hasMeasurement, measured_data_node))

            output_base_jsonld = os.path.join(output_dir_jsonld, f"annotated_{sample_id}")
            output_base_ttl = os.path.join(output_dir_ttl, f"annotated_{sample_id}")

            #Serializing in jsonld and ttl
            g.serialize(output_base_jsonld + ".jsonld", format="json-ld")
            g.serialize(output_base_ttl + ".ttl", format="turtle")