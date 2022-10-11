from deposit_gui.dgui.dcmodel import DCModel

from deposit import (AbstractDType)
from deposit.datasource import (AbstractDatasource, Memory)
from deposit.utils.fnc_files import (as_url)
from deposit.query.parse import (remove_bracketed_all)

from collections import defaultdict
from natsort import natsorted

class LCModel(DCModel):
	
	NAME_ID = "Custom_Id"  # name of descriptor which represents the id of a unique sample
	
	def __init__(self, cmain):
		
		DCModel.__init__(self, cmain)
		
		self._descriptors = []
		self._default_descriptors = None
		self._multi_descriptors = {} # {name: group_name, ...}
		self._attributes = []
	
	# ---- Signal handling
	# ------------------------------------------------------------------------
	def on_set_descriptors(self, data):
		# data = [[name, chain], ...];
		# 	chain = "Class.Descriptor" or "Class.Relation.Class.Descriptor"
		
		pass
		
	def on_set_attributes(self, data):
		# data = [(label, ctrl_type, name), ...]
		
		pass
	
	# ---- get/set
	# ------------------------------------------------------------------------
	def get_default_descriptors(self):
		# returns [[name, chain], ...]
		
		if self._default_descriptors is None:
			self._default_descriptors = []
			self._multi_descriptors = {} # {name: group_name, ...}
			for name, chain in [
				[self.NAME_ID,				"Sample.Id"],
				["Profile_Rim",				"Sample.Rim"],
				["Profile_Bottom",			"Sample.Bottom"],
				["Profile_Lid",				"Sample.Lid"],
				["Profile_Radius",			"Sample.Radius"],
				["Profile_Geometry",		"Sample.Profile"],
				["Profile_Radius_Point",	"Sample.Radius_Point"],
				["Profile_Rim_Point",		"Sample.Rim_Point"],
				["Profile_Bottom_Point",	"Sample.Bottom_Point"],
				["Profile_Left_Side",		"Sample.Left_Side"],
				["ScaleBar_Offset",			"Sample.ScaleBar_Offset"],
				["ScaleBar_Length",			"Sample.ScaleBar_Length"],
				["Reconstruction",			"Sample.Reconstruction"],
				["Settings",				"Sample.Settings"],
				["Date_Created",			"Sample.Date_Created"],
				["Date_Modified",			"Sample.Date_Modified"],
				["SW_Version",				"Sample.SW_Version"],
				["Settings",				"Sample.Settings"],
				["Detail_Geometry",			"Sample.Drawn.Detail.Geometry"],
				["Detail_Filled",			"Sample.Drawn.Detail.Filled"],
				["Break_Geometry",			"Sample.Drawn.Break.Geometry"],
				["Inflection_Geometry",		"Sample.Drawn.Inflection.Geometry"],
				["Inflection_Dashed",		"Sample.Drawn.Inflection.Dashed"],
				["Arc_Geometry",			"Sample.Drawn.Arc.Geometry"],
				["Photo_Image",				"Sample.Drawn.Photo.Image"],
				["Photo_Mask",				"Sample.Drawn.Photo.Mask"],
				["Photo_Position",			"Sample.Drawn.Photo.Position"],
				["Photo_Angle",				"Sample.Drawn.Photo.Angle"],
				["Photo_Scale",				"Sample.Drawn.Photo.Scale"],
				["Annotation_Geometry",		"Sample.Drawn.Annotation.Geometry"],
				["Annotation_Name",			"Sample.Drawn.Annotation.Name"],
				["Measure_Geometry",		"Sample.Drawn.Measure.Geometry"],
				["Measure_Name",			"Sample.Drawn.Measure.Name"],
				["Measure_Value",			"Sample.Drawn.Measure.Value"],
			]:
				self._default_descriptors.append([name, chain])
				parsed = self.parse_chain(chain)
				if len(parsed) == 4:
					self._multi_descriptors[name] = parsed[2]
		
		return self._default_descriptors
	
	def get_default_attributes(self):
		# returns [(label, ctrl_type, name), ...]
		
		return [
			["Sample ID", "LineEdit", self.NAME_ID],
		]
	
	def set_descriptors(self, data):
		# data = [[name, chain], ...];
		# 	chain = "Class.Descriptor" or "Class.Relation.Class.Descriptor"
		
		data = data.copy()
		default_descriptors = self.get_default_descriptors()
		data_lookup = dict(data)
		for name, chain in default_descriptors:
			if name not in data_lookup:
				data.append([name, chain])
		self._descriptors = data
		
		self.on_set_descriptors(data)
	
	def get_descriptors(self):
		# returns [[name, chain], ...];
		
		return self._descriptors
	
	def set_attributes(self, data):
		# data = [(label, ctrl_type, name), ...]
		
		data = data.copy()
		data_lookup = set([name for _, _, name in data])
		for label, ctrl_type, name in self.get_default_attributes():
			if name not in data_lookup:
				data.append([label, ctrl_type, name])
		self._attributes = data
		
		self.on_set_attributes(data)
	
	def get_attributes(self):
		# returns [(label, ctrl_type, name), ...]
		
		return self._attributes
	
	def to_settings_dict(self):
		
		return dict(
			descriptors = self.get_descriptors(),
			attributes = self.get_attributes(),
		)
	
	def from_settings_dict(self, data):
		
		if "descriptors" in data:
			self.set_descriptors(data["descriptors"])
		if "attributes" in data:
			self.set_attributes(data["attributes"])
	
	def parse_chain(self, chain):
		
		chain, bracketed = remove_bracketed_all(chain)
		chain = chain.split(".")
		for i, fragment in enumerate(chain):
			for key in bracketed:
				chain[i] = chain[i].replace(key, bracketed[key][1:-1])
		if len(chain) == 2:
			cls, descr = chain
			return [cls, descr]
			
		elif len(chain) == 4:
			class1, rel, class2, descr = chain
			return [class1, rel, class2, descr]
		
		return []
	
	def get_data_structure(self, default_only = False, no_default = False):
		# returns classes, descriptors, relations
		#	classes = [Class, ...]
		#	descriptors = [(name, Class, Descriptor), ...]
		#	relations = set((Class1, Relation, Class2), ...)
		
		if default_only:
			descriptors_ = self.get_default_descriptors()
		else:
			descriptors_ = self._descriptors
		
		if no_default:
			except_names = set()
			for name, _ in self.get_default_descriptors():
				except_names.add(name)
			collect = []
			for name, chain in descriptors_:
				if name in except_names:
					continue
				collect.append((name, chain))
			descriptors_ = collect
		
		classes = []
		descriptors = []
		relations = set()
		for name, chain in descriptors_:
			parsed = self.parse_chain(chain)
			if len(parsed) == 2:
				cls, descr = parsed
				if (name, cls, descr) not in descriptors:
					descriptors.append((name, cls, descr))
				if cls not in classes:
					classes.append(cls)
			elif len(parsed) == 4:
				class1, rel, class2, descr = parsed
				if class1 not in classes:
					classes.append(class1)
				if class2 not in classes:
					classes.append(class2)
				if (name, class2, descr) not in descriptors:
					descriptors.append((name, class2, descr))
				relations.add((class1, rel, class2))
		
		return classes, descriptors, relations
	
	def create_data_structure(self):
		# returns descr_lookup, relations
		#	descr_lookup = {name: (Class, Descriptor), ...}
		#	relations = set((Class1, Relation, Class2), ...)
		
		classes, descriptors, relations = self.get_data_structure()
		
		cls_lookup = {}
		descr_lookup = {}
		for name in classes:
			cls_lookup[name] = self.add_class(name)
		for name, cls, descr in descriptors:
			cls_lookup[cls].set_descriptor(descr)
			descr_lookup[name] = (cls, descr)
		for cls1, rel, cls2 in relations:
			cls_lookup[cls1].add_relation(cls2, rel)
		
		return descr_lookup, relations
	
	def get_cls_descr(self, name):
		
		_, descriptors, _ = self.get_data_structure()
		for name_, cls, descr in descriptors:
			if name_ == name:
				return cls, descr
		return None, None
	
	def find_sample_id(self, sample_id):
		# returns obj_id if sample_id exists, else None
		
		if sample_id is None:
			return None
		
		sample_cls, sample_descr = self.get_cls_descr(self.NAME_ID)
		if (sample_cls is None) or (sample_descr is None):
			return None
		
		cls = self.get_class(sample_cls)
		if cls is None:
			return None
		
		sample_id = str(sample_id).strip()
		for obj in cls.get_members(direct_only = True):
			value = obj.get_descriptor(sample_descr)
			if (value is None) or isinstance(value, AbstractDType):
				continue
			if str(value).strip() == sample_id:
				return obj.id
		
		return None
	
	def clear_data(self, primary_obj, keep_default = False):
		# returns objects_changed, objects_deleted
		#	objects_changed / objects_deleted = set(obj_id, ...)
		
		objects_changed = set()
		objects_deleted = set()
		
		_, descriptors, relations = self.get_data_structure(no_default = keep_default)
		if keep_default:
			default_classes = set()
		else:
			default_classes, _, _ = self.get_data_structure(default_only = True)
			default_classes = set(default_classes)
		descr_lookup = {}
		for name, cls, descr in descriptors:
			descr_lookup[name] = (cls, descr)
		
		primary_cls, _ = self.get_cls_descr(self.NAME_ID)
		
		keep_names = set()
		if keep_default:
			for name, _ in self.get_default_descriptors():
				keep_names.add(name)
		
		# delete existing descriptors from descr_lookup
		for name in descr_lookup:
			if name in keep_names:
				continue
			cls, descr = descr_lookup[name]
			if cls == primary_cls:
				primary_obj.del_descriptor(descr)
				objects_changed.add(primary_obj.id)
		
		# delete existing relations from supplied relations
		rel_lookup = {}
		for cls1, rel, cls2 in relations:
			if cls1 == primary_cls:
				rel_lookup[cls2] = rel
			elif cls2 == primary_cls:
				rel_lookup[cls1] = self.reverse_relation(rel)
		rel_classes = set(rel_lookup.keys())
		to_del_rels = set()
		to_del_objs = set()
		for obj_tgt, rel in primary_obj.get_relations():
			obj_classes = set(obj_tgt.get_classes())
			obj_classes = rel_classes.intersection(
				[cls.name for cls in obj_classes]
			)
			if not obj_classes:
				continue
			if rel not in set([rel_lookup[cls] for cls in obj_classes]):
				continue
			has_other_rels = False
			for obj2, _ in obj_tgt.get_relations():
				if obj2 != primary_obj:
					has_other_rels = True
					break
			if (not has_other_rels) and obj_classes.intersection(default_classes):
				to_del_objs.add(obj_tgt.id)
			else:
				to_del_rels.add((obj_tgt, rel))
		for obj_tgt, rel in to_del_rels:
			primary_obj.del_relation(obj_tgt, rel)
			objects_changed.add(obj_tgt.id)
		for obj_id in to_del_objs:
			self.del_object(obj_id)
			objects_deleted.add(obj_id)
		
		return objects_changed, objects_deleted
	
	def store_data(self, data, obj_id = None, silent = False, keep_default = False):
		# data = {(name, chain): value, key: [{(name, chain): value, ...}, ...], ...}
		
		def convert_value(value):
			
			if isinstance(value, bool):
				return int(value)
			return value
		
		objects_changed = set()
		classes_changed = set()
		objects_added = set()
		objects_deleted = set()
		
		self._model.blockSignals(True)
		if (not silent) and (self._progress is not None):
			self._progress.show("Storing Drawing")
			self._progress.update_state(value = 1, maximum = 3)
		
		descr_lookup, relations = self.create_data_structure()
		# descr_lookup = {name: (Class, Descriptor), ...}
		# relations = set((Class1, Relation, Class2), ...)
		for name in descr_lookup:
			cls, descr = descr_lookup[name]
			classes_changed.add(cls)
			classes_changed.add(descr)
		
		if (not silent) and (self._progress is not None):
			self._progress.update_state(value = 2)
		primary_cls, _ = descr_lookup[self.NAME_ID]
		if obj_id is None:
			primary_obj = self.get_class(primary_cls).add_member()
			objects_added.add(primary_obj.id)
		else:
			primary_obj = self.get_object(obj_id)
			objects_changed_, objects_deleted_ = self.clear_data(primary_obj, keep_default)
			objects_changed.update(objects_changed_)
			objects_deleted.update(objects_deleted_)
		
		# store data
		row_data = {}  # {(Class name, Descriptor name): value, ...}
		for key in data:
			if not isinstance(data[key], list):
				name, _ = key
				row_data[descr_lookup[name]] = convert_value(data[key])
		_, added = self.add_data_row(
			row_data, 
			relations, 
			unique = set([primary_cls]), 
			existing = {primary_cls: primary_obj},
			return_added = True,
		)
		for cls in added:
			classes_changed.add(cls)
			objects_added.add(added[cls].id)
		
		rel_lookup = {}
		for cls1, rel, cls2 in relations:
			if cls1 == primary_cls:
				rel_lookup[cls2] = self.reverse_relation(rel)
			elif cls2 == primary_cls:
				rel_lookup[cls1] = rel
		
		for key in data:
			if isinstance(data[key], list):
				for item in data[key]:
					row_data = {}
					for key2 in item:
						name, _ = key2
						row_data[descr_lookup[name]] = convert_value(item[key2])
					_, added = self.add_data_row(
						row_data, 
						relations,
						return_added = True,
					)
					for cls in added:
						classes_changed.add(cls)
						if cls in rel_lookup:
							added[cls].add_relation(primary_obj, rel_lookup[cls])
						objects_added.add(added[cls].id)
		if (not silent) and (self._progress is not None):
			self._progress.update_state(value = 3)
			self._progress.stop()
		self._model.blockSignals(False)
		if not silent:
			self.on_changed(objects_changed, classes_changed)
			self.on_added(objects_added, [])
			self.on_deleted(objects_deleted, [])
		
	def get_load_lookups(self):
		# returns name_lookup, class_descriptors, primary_class, rel_primary, rel_chains
		# name_lookup = {(Class, Descriptor): name, ...}
		# class_descriptors = {Class: [Descriptor, ...], ...}
		# primary_class = name of Sample class
		# rel_primary = {Class: relation, ...}
		
		_, descriptors, relations = self.get_data_structure()
		# descriptors = [(name, Class, Descriptor), ...]
		# relations = set((Class1, Relation, Class2), ...)
		
		name_lookup = {}  # {(Class, Descriptor): name, ...}
		class_descriptors = defaultdict(set)  # {Class: [Descriptor, ...], ...}
		primary_class = None
		for name, cls, descr in descriptors:
			name_lookup[(cls, descr)] = name
			class_descriptors[cls].add(descr)
			if name == self.NAME_ID:
				primary_class = cls
		rel_primary = {}
		rel_other = set()
		for cls1, rel, cls2 in relations:
			if cls1 == primary_class:
				rel_primary[cls2] = rel
			elif cls2 == primary_class:
				rel_primary[cls1] = self.reverse_relation(rel)
			else:
				rel_other.add((cls1, rel, cls2))
				rel_other.add((cls2, self.reverse_relation(rel), cls1))
		
		rel_chains = []
		for cls1 in rel_primary:
			chain = [(rel_primary[cls1], cls1)]
			cls_last = cls1
			done = set([cls1])
			while True:
				found = False
				for cls1_, rel, cls2 in rel_other:
					if cls2 in done:
						continue
					if cls1_ == cls_last:
						chain.append((rel, cls2))
						done.add(cls2)
						cls_last = cls2
						found = True
				if not found:
					break
			if len(chain) > 1:
				rel_chains.append(chain)
		
		return name_lookup, class_descriptors, primary_class, rel_primary, rel_chains
	
	def load_object_data(
		self, obj_id, name_lookup, class_descriptors, 
		primary_class, rel_primary, rel_chains,
	):
		# name_lookup = {(Class, Descriptor): name, ...}
		# class_descriptors = {Class: [Descriptor, ...], ...}
		# primary_class = name of Sample class
		# rel_primary = {Class: relation, ...}
		# rel_chains = [[(relation, Class), ...], ...]
		
		def get_chained(obj, label, cls):
			
			for obj_tgt, label_ in obj.get_relations():
				if label_ == label:
					return obj_tgt
			return None
		
		def collect_data(key, name_lookup, value, data, data_rel):
			
			if value is None:
				return
			group = None
			if name_lookup[key] in self._multi_descriptors:
				group = self._multi_descriptors[name_lookup[key]]
			if group is None:
				data[name_lookup[key]] = value
			else:
				if group not in data_rel:
					data_rel[group] = {}
				data_rel[group][name_lookup[key]] = value
		
		rel_classes = set([cls for cls, _ in name_lookup.keys()])
		primary_rels = set(rel_primary.values())
		chain_classes = set()
		for chain in rel_chains:
			label, cls = chain[0]
			primary_rels.add(label)
			chain_classes.add(cls)
		
		data = {}
		obj = self.get_object(obj_id)
		
		for descr in obj.get_descriptors():
			key = (primary_class, descr.name)
			if key in name_lookup:
				data[name_lookup[key]] = obj.get_descriptor(descr)
		
		for obj_tgt, label in obj.get_relations():
			if label not in primary_rels:
				continue
			
			data_rel = {}
			
			obj_classes = set([cls.name for cls in obj_tgt.get_classes()])
			for cls in rel_classes.intersection(obj_classes):
				for descr in obj_tgt.get_descriptors():
					key = (cls, descr.name)
					if key in name_lookup:
						collect_data(key, name_lookup, obj_tgt.get_descriptor(descr), data, data_rel)
			
			for cls in chain_classes.intersection(obj_classes):
				for chain in rel_chains:
					if chain[0] != (label, cls):
						continue
					for label2, cls2 in chain[1:]:
						obj_tgt = get_chained(obj_tgt, label2, cls2)
						if obj_tgt is None:
							continue
						for descr in obj_tgt.get_descriptors():
							key = (cls2, descr.name)
							if key in name_lookup:
								collect_data(key, name_lookup, obj_tgt.get_descriptor(descr), data, data_rel)
			
			for cls in data_rel:
				if cls not in data:
					data[cls] = []
				data[cls].append(data_rel[cls])
		
		return data
	
	def load_data(self, obj_id):
		# returns data
		#	data = {name: value, key: [{name: value, ...}, ...], ...}
		
		name_lookup, class_descriptors, primary_class, rel_primary, rel_chains = \
			self.get_load_lookups()
		
		data = self.load_object_data(
			obj_id, name_lookup, class_descriptors, 
			primary_class, rel_primary, rel_chains,
		)
		
		return data
	
	def delete_drawings(self, obj_ids):
		
		objects_changed = set()
		classes_changed = set()
		objects_deleted = set()
		
		self._model.blockSignals(True)
		for obj_id in obj_ids:
			primary_obj = self.get_object(obj_id)
			if primary_obj is None:
				continue
			objects_changed_, objects_deleted_ = self.clear_data(primary_obj)
			objects_changed.update(objects_changed_)
			objects_deleted.update(objects_deleted_)
			self.del_object(obj_id)
			objects_deleted.add(obj_id)
		self._model.blockSignals(False)
		self.on_changed(objects_changed, classes_changed)
		self.on_deleted(objects_deleted, [])
	
	
	# ---- Deposit
	# ------------------------------------------------------------------------
	def get_query(self, querystr, silent = False):
		
		if (not silent) and (self._progress is not None):
			self._progress.show("Processing Query")
		query = self._model.get_query(
			querystr, 
			progress = self._progress if not silent else None,
		)
		if (not silent) and (self._progress is not None):
			self._progress.stop()
		return query
	
	def get_descriptor_values(self):
		# direct_only = if True, don't return members of subclasses
		#
		# returns {name: [value, ...], ...}
		
		_, descriptors, _ = self.get_data_structure()
		lookup = {}
		for name, cls, descr in descriptors:
			lookup[name] = (cls, descr)
		data = {}
		for name in lookup:
			class_name, descriptor_name = lookup[name]
			data[name] = []
			for value in self._model.get_descriptor_values(
				class_name, descriptor_name
			):
				if not isinstance(value, AbstractDType):
					data[name].append(str(value))
			data[name] = natsorted(data[name])
		return data

