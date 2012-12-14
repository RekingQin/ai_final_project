#-*- coding: big5 -*-
import os.path
import subprocess
import random

# Information:
#   - Mahjoing rule: http://ezmjtw.tripod.com/mahjong16-big5.htm
#   - �±N�򥻳N�y���^���Ӫ�: http://www.xqbase.com/other/mahjongg_english.htm
#                            http://liangliangliang.pixnet.net/blog/post/15530445-%E2%99%A5%E9%BA%BB%E5%B0%87%E8%8B%B1%E6%96%87mahjong-%E5%9F%BA%E6%9C%AC%E5%96%AE%E5%AD%97%E7%AF%87%E2%99%A5
#   - �±N�J�P�ޥ�: http://ezmjtw.tripod.com/mahjongskill-big5.htm
# Change history:
#   - 2012/11/30 John K Lee
#     * Fix bug in situation of dropping card will ignore winner.
#     * Replace some trivial nonu with proper nonu.
#     * Add SmartAgent.py
#     * Modify run.py to read loop from interactive conosle.
#     * Fix bug in siguation of gang which will cause long hand (�j�ۤ�)
#   - 2012/12/01 John K Lee
#     * Add static function:PreWinTiles into GameBoard class to check win tile(s) of an Agent object.
#   - 2012/12/02 John K Lee
#     * Add IAgent.py to provide interactive mode agent.
#   - 2012/12/03 John K Lee
#     * Fix bug in situation of dropping card which will cause short hand (�p�ۤ�)
#     * Add JAgent.py
#   - 2012/12/04 John K Lee
#     * Fix bug which Agent with wrong=True attribute will cause follow playing stop.
#
# 0) Global function
def searchWithEye(clist):
	if len(clist)==0:
		return False
	elif len(clist)>2:
		if clist[0]==clist[1]==clist[2]:
			# �� (Triplet)
			return searchWithEye(clist[3:]) or searchNoEye(clist[2:])
		elif clist[0]!=clist[1]:
			val = clist[0]
			if (val+1 in clist) and (val+2 in clist):
				clist.remove(val)
				clist.remove(val+1)
				clist.remove(val+2)
				clist.sort()
				return searchWithEye(clist)
			else:
				return False
		else:
			val = clist[0]
			if clist.count(val+1)==2 and clist.count(val+2)==2:
				# �� (Sequence)
				return searchWithEye(clist[6:]) or searchNoEye(clist[2:])
			else:    
				return searchNoEye(clist[2:])
	elif len(clist)==2:
		return clist[0] == clist[1]
	else:
		return False
    
def searchNoEye(clist):
	if len(clist)==0:
		return True
	elif len(clist)>2:
		rst = False
		if clist[0]==clist[1]==clist[2]:
			# �� (Triplet)
			del clist[0:3]
			return searchNoEye(clist)
		elif clist[0]!=clist[1]:
			# �� (Sequence)
			val = clist[0]
			if (val+1 in clist) and (val+2 in clist):
				clist.remove(val)
				clist.remove(val+1)
				clist.remove(val+2)
				clist.sort()
				return searchNoEye(clist)
			else:
				return False
		else:
			val = clist[0]
			if clist.count(val+1)==2 and clist.count(val+2)==2:
				del clist[0:6]
				clist.sort()
				return searchNoEye(clist)
			else:    
				return False
	else:
		return False

def toCListStr(clist):
	cstr = '['
	if len(clist) > 0:
		cstr+="{0:s}".format(clist[0])
		for i in range(1, len(clist)):
			cstr+=" {0:s}".format(clist[i])
	cstr+=']'
	return cstr

# 1) Class definition
class GameBoard:
	def __init__(self):
		self.bamb_list = [] # ���l
		self.wang_list = [] # �U�r
		self.tube_list = [] # ���l
		self.flow_list = [] # ��P
		self.word_list = [] # �r�P (���o��)
		self.wind_list = [] # ���P
		self.aget_list = [] # ���a
		self.drop_list = [] # ����
		self.fwind_list = []
		self.fword_list = []
		self.fwang_list = []
		self.ftube_list = []
		self.fbamb_list = []
		self.play_turn = 0  # �N�P���a
		self.fwind_list.append('�F')
		self.fwind_list.append('��')
		self.fwind_list.append('�n')
		self.fwind_list.append('�_')
		self.fword_list.append('��')
		self.fword_list.append('�o')
		self.fword_list.append('��')
		self.win_round = {}
		self.pwin_round = {}
		for i in range(1,10):
			self.fwang_list.append('{0}�U'.format(i))        
			self.ftube_list.append('{0}��'.format(i))
			self.fbamb_list.append('{0}��'.format(i))
		 
		self.win_agent = None
		self.drop_record = {}
		self.wrong_count = 0
		self.play_count = 0
		#self.shuffle()        

	def rightOpponent(self, agent):
		if agent in self.aget_list:
			curpos = self.aget_list.index(agent)
			return self.aget_list[(curpos+1) % len(self.aget_list)]

	def leftOpponent(self, agent):
		if agent in self.aget_list:
			curpos = self.aget_list.index(agent)
			if curpos > 0:
				return self.aget_list[(curpos-1) % len(self.aget_list)]
			else:
				return self.aget_list[len(self.aget_list) - 1]

	def appendAgent(self, agent):
		self.aget_list.append(agent)

	@staticmethod
	def ToIntList(clist):
		tlist = []
		for e in clist:
			tlist.append(int(e[0:1]))
		return tlist

	# �T�{ clist �O�_������. clist �����O���㪺 meld+����.
	@staticmethod
	def HasEye(ctype, clist):
		list_len = len(clist)
		if list_len > 1:
			if ctype <=3:
				for e in set(clist):
					if clist.count(e) == 2:                        
						if searchWithEye(GameBoard.ToIntList(clist)):
							return e
			else:
				GameBoard.RemoveTriplet(clist[:])
				if len(clist)==2 and (clist[0]==clist[1]):
					return clist[0]

	# ���� clist ���Ҧ� Triplet.
	@staticmethod
	def RemoveTriplet(clist):
		p=0
		while p+2<len(clist):
			if clist[p]==clist[p+1] and clist[p+1]==clist[p+2]:
				del clist[p:p+3]
			else:
				p+=1            

	# �q check_tuple = (card_type, card_list) ����X�i�Hť�P�� Tile
	# Input: check_tuple = (card_type, card_list)
	# Output: win tile list
	@staticmethod
	def searchWTiles(chek_tuple, hasEye=True):
		tiles=[]
		if chek_tuple[0]==1:
			for i in range(1,10):                    
				c_list = []
				for e in chek_tuple[1]:
					c_list.append(int(e[0:1]))
				c_list.append(i)
				c_list.sort()
				if hasEye and searchWithEye(c_list):
					tiles.append('{0}�U'.format(i))
				elif not hasEye and searchNoEye(c_list):
					tiles.append('{0}�U'.format(i))
		elif chek_tuple[0]==2:
			for i in range(1,10):                    
				c_list = []
				for e in chek_tuple[1]:
					c_list.append(int(e[0:1]))
				c_list.append(i)
				c_list.sort()
				if hasEye and searchWithEye(c_list):
					tiles.append('{0}��'.format(i))
				elif not hasEye and searchNoEye(c_list):
					tiles.append('{0}��'.format(i))
		elif chek_tuple[0]==3:
			for i in range(1,10):                    
				c_list = []
				for e in chek_tuple[1]:
					c_list.append(int(e[0:1]))
				c_list.append(i)
				c_list.sort()
				if hasEye and searchWithEye(c_list):
					tiles.append('{0}��'.format(i))
				elif not hasEye and searchNoEye(c_list):
					tiles.append('{0}��'.format(i))
		elif chek_tuple[0]==4: # ���o��
			GameBoard.RemoveTriplet(chek_tuple[1])
			if hasEye and (len(chek_tuple[1])==1):
				tiles.append(chek_tuple[1][0])
			elif not hasEye and (len(chek_tuple[1])==2):
				if chek_tuple[0] == chek_tuple[1]:
					return chek_tuple[0]
		elif chek_tuple[0]==5: # ���P
			GameBoard.RemoveTriplet(chek_tuple[1])
			if(len(chek_tuple[1])==1):
				tiles.append(chek_tuple[1][0])
			elif not hasEye and (len(chek_tuple[1])==2):
				if chek_tuple[0] == chek_tuple[1]:
					return chek_tuple[0]
		return tiles

	# �T�{ Agent ��ť�P tiles
	# Input: Agent object
	# Output: Tile list which contains win tile
	# Example:
	#       Input=Agent=[1�U 2�U 3�U 4�U 4�U 1�� 3�� 3�� 3�� 3�� ] / [] / []
	#       Output=['2��']
	@staticmethod
	def PreWinTiles(agent):
		#tiles = []
		meld_list = []
		chek_list = []
		if len(agent.wang_list) > 0:
			if len(agent.wang_list)%3==0:
				meld_list.append(agent.wang_list[:])
			else:
				chek_list.append((1, agent.wang_list[:]))
			
		if len(agent.tube_list) > 0:
			if len(agent.tube_list)%3==0:
				meld_list.append(agent.tube_list[:])
			else:
				chek_list.append((2, agent.tube_list[:]))

		if len(agent.bamb_list) > 0:
			if len(agent.bamb_list)%3==0:
				meld_list.append(agent.bamb_list[:])
			else:
				chek_list.append((3, agent.bamb_list[:]))

		if len(agent.word_list) > 0:
			if len(agent.word_list)%3==0:
				meld_list.append(agent.word_list[:])
			else:
				chek_list.append((4, agent.word_list[:]))

		if len(agent.wind_list) > 0:
			if len(agent.wind_list)%3==0:
				meld_list.append(agent.wind_list[:])
			else:
				chek_list.append((5, agent.wind_list[:]))

		# 1) Check impossible composition
		if len(chek_list) > 2:
			return []

		for clist in meld_list:
			ctype = GameBoard.CardType(clist[0])
			if ctype<4:                
				if not searchNoEye(GameBoard.ToIntList(clist)):
					return []
			else:
				GameBoard.RemoveTriplet(clist)
				if(len(clist)!=0):
					return []

		# 2) Start to look for possible tiles to win
		if len(chek_list)==2: 
			eye_1 = GameBoard.HasEye(chek_list[0][0], chek_list[0][1])
			eye_2 = GameBoard.HasEye(chek_list[1][0], chek_list[1][1])
			if eye_1 and eye_2:
				#print('eye_1={0}; eye_2={1}'.format(eye_1, eye_2))
				#print('check {0}'.format(eye_1))
				tiles = []
				chek_tuple = chek_list[0]
				chek_tuple[1].append(eye_1)
				chek_tuple[1].sort()
				if chek_tuple[0]<=3:
					if searchNoEye(GameBoard.ToIntList(chek_tuple[1])):
						tiles.append(eye_1)
					else:
						return []
				else:
					GameBoard.RemoveTriplet(chek_tuple[1])
					if len(chek_tuple[1]) == 0:
						tiles.append(eye_1)
					else:
						return []                
				chek_tuple = chek_list[1]
				chek_tuple[1].append(eye_2)
				chek_tuple[1].sort()
				#print('check {0}->{1}'.format(eye_2, chek_tuple[1]))
				if chek_tuple[0]<=3:
					if searchNoEye(GameBoard.ToIntList(chek_tuple[1])):
						tiles.append(eye_2)
					else:
						return []
				else:
					GameBoard.RemoveTriplet(chek_tuple[1])
					if len(chek_tuple[1]) == 0:
						tiles.append(eye_2)
					else:
						return []
				return tiles
			elif eye_1:                
				chek_tuple = chek_list[0]
				#print('Check eye_1={0}={1}!'.format(eye_1, chek_tuple[1]))
				if chek_tuple[0]<=3:
					if not searchWithEye(GameBoard.ToIntList(chek_tuple[1])):
						return []
				else:
					GameBoard.RemoveTriplet(chek_tuple[1])
					if len(chek_tuple[1]) != 0:
						return []
				#print('Pass check. Search tile...{0}'.format(chek_list[1]))
				return GameBoard.searchWTiles(chek_list[1], hasEye=False)
			elif eye_2:
				#print('Check eye_2={0}={1}!'.format(eye_2, chek_tuple[1]))
				chek_tuple = chek_list[1]
				if chek_tuple[0]<=3:
					if not searchWithEye(GameBoard.ToIntList(chek_tuple[1])):
						return []
				else:
					GameBoard.RemoveTriplet(chek_tuple[1])
					if len(chek_tuple[1]) != 0:
						return []
				#print('Pass check. Search tile {0}...'.format(chek_list[0]))
				return GameBoard.searchWTiles(chek_list[0], hasEye=False)
			else:
				return []
		else:
			if len(chek_list) > 0:
				chek_tuple = chek_list[0]
				return GameBoard.searchWTiles(chek_tuple)
		return []
		
	# ���U�����U�i�ഫ���
	# Input: ���U��. Ex. '1�U' ,'2��' ,'3��'.
	# Output: ���U�����U�@�i. ���p�G�O 9��/�U/�� �Τ��O���U��, �h��^ None.
	# Example: Input='1�U' ; Output='2�U'
	@staticmethod
	def NextCard(card):
		ctype = GameBoard.CardType(card)
		number = int(card[:1])        
		if ctype==1:
			if number<9:
				return "{0}{1}".format(number+1, '�U')
		elif ctype==2:
			if number<9:
				return "{0}{1}".format(number+1, '��')
		elif ctype==3:
			if number<9:
				return "{0}{1}".format(number+1, '��')

	# ���U�����W�i�ഫ���
	# Input: ���U��. Ex. '1�U' ,'2��' ,'3��'.
	# Output: ���U�����W�@�i. ���p�G�O 9��/�U/�� �Τ��O���U��, �h��^ None.
	# Example: Input='2��' ; Output='1��'
	@staticmethod
	def PrevCard(card):
		ctype = GameBoard.CardType(card)
		number = int(card[:1])        
		if ctype==1:
			if number>1:
				return "{0}{1}".format(number-1, '�U')
		elif ctype==2:
			if number>1:
				return "{0}{1}".format(number-1, '��')
		elif ctype==3:
			if number>1:
				return "{0}{1}".format(number-1, '��')
			
	# �J�P�P�_
	@staticmethod
	def GoalState(agent, card):
		# http://www.programmer-club.com/showSameTitleN/gameprogram/3310.html
		eyePair = False
		tbamb_list = [] # ���l
		for e in agent.bamb_list:
			tbamb_list.append(int(e[0:1]))
		twang_list = [] # �U�r
		for e in agent.wang_list:
			twang_list.append(int(e[0:1]))    
		ttube_list = [] # ���l
		for e in agent.tube_list:
			ttube_list.append(int(e[0:1]))    
		tword_list = agent.word_list[:] # �r�P (���o��)
		twind_list = agent.wind_list[:] # ���P
		ctype = GameBoard.CardType(card)
		if ctype==1:
			twang_list.append(int(card[0:1]))
			twang_list.sort()
		elif ctype==2:
			ttube_list.append(int(card[0:1]))
			ttube_list.sort()
		elif ctype==3:
			tbamb_list.append(int(card[0:1]))
			tbamb_list.sort()
		elif ctype==4:
			tword_list.append(card)
			tword_list.sort()
		elif ctype==5:
			twind_list.append(card)
			twind_list.sort()

		# Filter impossible composition
		bamb_len = len(tbamb_list)
		wang_len = len(twang_list)
		tube_len = len(ttube_list)
		word_len = len(tword_list)
		dirt_len = len(twind_list)
		if (bamb_len%3+wang_len%3+tube_len%3+word_len%3+dirt_len%3)!=2 or \
		   bamb_len==1 or wang_len==1 or tube_len==1 or word_len==1 or dirt_len==1:
			return False
		
		# �T�{ ���P    
		if dirt_len>0:
			GameBoard.RemoveTriplet(twind_list)
			if dirt_len==2: # ����
				if twind_list[0]!=twind_list[1]:
					return False
				else:
					eyePair=True
					del twind_list[:]
			else:
				return False
			
		# �T�{ �r�P
		if word_len>0:
			GameBoard.RemoveTriplet(tword_list)
			if word_len==2: # ����
				if tword_list[0]!=tword_list[1]:
					return False
				else:
					eyePair=True
					del tword_list[:]
			else:
				return False            

		# �T�{ ���l
		if bamb_len>0:
			if bamb_len%3 == 0: # ��/��
				if not searchNoEye(tbamb_list):
					return False
			else: # �t����
				if not searchWithEye(tbamb_list):
					return False

		# �T�{ �U�l
		if wang_len>0:
			if wang_len%3 == 0: # ��/��
				if not searchNoEye(twang_list):
					return False
			else: # �t����
				if not searchWithEye(twang_list):
					return False

		# �T�{ ���l
		if tube_len>0:
			if tube_len%3 == 0: # ��/��
				if not searchNoEye(ttube_list):
					return False
			else: # �t����
				if not searchWithEye(ttube_list):
					return False        
		return True

	@staticmethod
	def CardType(card):
		if card.endswith('�U'): return 1
		elif card.endswith('��'): return 2
		elif card.endswith('��'): return 3
		elif card in ['��', '�o', '��']: return 4
		elif card in ['�F', '�n', '��', '�_']: return 5
		else: return 6 # ��P

	# �}�l�C��    
	def play(self):
		self.play_count += 1
		self.shuffle()
		# Draw cards for each agent
		for agent in self.aget_list:
			agent.assignCard();
			print(agent)
		
			
		# Start game by assign card to each agent until one of them reach goal state
		i = 0
		while self.card_count>10 and not self.win_agent:
			agent = self.aget_list[int(self.play_turn)]
			self.play_turn = (self.play_turn+1)%len(self.aget_list)
			dcard = None
			if hasattr(agent, 'idraw'):
				dcard = agent.idraw()
			else:
				dcard = agent.draw()
			if hasattr(agent, 'wrong') and agent.wrong:
				print("[Debug] {0}->{1}".format(agent, agent.card_count))
				agent.wrong=False
				#subprocess.call('sleep 5s', shell=True) 
				self.wrong_count+=1
				break

			if dcard: self.disCard(agent, dcard)
			i+=1
			pwin_ac = 0
			print ""
			for agent in self.aget_list:
				print("[Turn{0}] {1}".format(i, agent))
				if hasattr(agent, 'pwin_flag') and agent.pwin_flag:
					pwin_ac+=1
			
			# Calculate prewin agent distribution
			if i in self.pwin_round:
				pwin_map = self.pwin_round[i]
				if pwin_ac in pwin_map:
					pwin_map[pwin_ac]+=1
				else:
					pwin_map[pwin_ac]=1
			else:
				pwin_map = {}
				pwin_map[pwin_ac] = 1
				self.pwin_round[i] = pwin_map

		if self.win_agent:
			print("result... Agent({0}) win the game!".format(self.win_agent.name))
			if i in self.win_round:
				self.win_round[i] += 1
			else:
				self.win_round[i] = 1
		else:
			print("result... �y��...")

	def _recordDrop(self, agent, card):
		if agent.name in self.drop_record:
			drop_list = self.drop_record[agent.name]
			drop_list.append(card)
			drop_list.sort()
		else:
			drop_list = []
			drop_list.append(card)
			self.drop_record[agent.name] = drop_list

	# ��P�����, callback by agent.
	def disCard(self, agent, card):
		self._recordDrop(agent, card)
		# ���@�a�i�H���Ӷ��ǨM�w�n���n�I�P

		# �T�{���S���H�w�g�J
		next_pos = self.aget_list.index(agent)+1
		for sft in range(len(self.aget_list)-1):
			other_agent = self.aget_list[(next_pos+sft)%len(self.aget_list)]
			if GameBoard.GoalState(other_agent, card):
				self.win_agent = other_agent
				other_agent.win_card = card
				other_agent.win+=1
				agent.lose+=1
				#print("\t[Test] Agent({0}) �J�P {1}!!!".format(other_agent.name, card))
				return
				

		# ���@�a�i�H���Ӷ��ǨM�w�n���n�I�P
		rtv = None
		next_pos = self.aget_list.index(agent)+1
		for sft in range(len(self.aget_list)-1):
			other_agent = self.aget_list[(next_pos+sft)%len(self.aget_list)]
			ctype = GameBoard.CardType(card)
			if ctype==1:
				count = other_agent.wang_list.count(card)
				if count>1:
					rtv = other_agent.pong(agent, ctype, count, card)
			elif ctype==2:
				count = other_agent.tube_list.count(card)
				if count>1:
					rtv = other_agent.pong(agent, ctype, count, card)
			elif ctype==3:
				count = other_agent.bamb_list.count(card)
				if count>1:
					rtv = other_agent.pong(agent, ctype, count, card)
			elif ctype==4:
				count = other_agent.word_list.count(card)
				if count>1:
					rtv = other_agent.pong(agent, ctype, count, card)
			elif ctype==5:
				count = other_agent.wind_list.count(card)
				if count>1:
					rtv = other_agent.pong(agent, ctype, count, card)
				
			if rtv: # ���H�I
				self.play_turn = (self.aget_list.index(other_agent)+1) % len(self.aget_list)
				self.disCard(other_agent, rtv)                    
				return
						

		# �U�a�i�H�M�w�n���n�Y�P
		next_agent = self.aget_list[(self.aget_list.index(agent)+1) % len(self.aget_list)]
		#print("\t[Test] next agent={0}...".format(next_agent.name))
		ctype = GameBoard.CardType(card)
		eat_list = []
		rtv = None # �Y�P���󪺵P
		if ctype==1:
			if card == '1�U' and \
			   ('2�U' in next_agent.wang_list) and \
			   ('3�U' in next_agent.wang_list):
				eat_list.append((['2�U', '3�U'], ['1�U', '2�U', '3�U']))
			elif card == '9�U' and \
			   ('7�U' in next_agent.wang_list) and \
			   ('8�U' in next_agent.wang_list):
				eat_list.append((['7�U', '8�U'], ['7�U', '8�U', '9�U']))                
			elif card == '2�U':
				if {'1�U', '3�U'} < set(next_agent.wang_list):
					eat_list.append((['1�U', '3�U'], ['1�U', '2�U', '3�U']))
				if {'3�U', '4�U'} < set(next_agent.wang_list):         
					eat_list.append((['3�U', '4�U'], ['2�U', '3�U', '4�U']))
			elif card == '8�U':
				if {'7�U', '9�U'} < set(next_agent.wang_list):
					eat_list.append((['7�U', '9�U'], ['7�U', '8�U', '9�U']))                    
				if {'6�U', '7�U'} < set(next_agent.wang_list):
					eat_list.append((['6�U', '7�U'], ['6�U', '7�U', '8�U']))                     
			elif card == '3�U':
				if {'1�U', '2�U'} < set(next_agent.wang_list):
					eat_list.append((['1�U', '2�U'], ['1�U', '2�U', '3�U']))                     
				if {'2�U', '4�U'} < set(next_agent.wang_list):
					eat_list.append((['2�U', '4�U'], ['2�U', '3�U', '4�U'])) 
				if {'4�U', '5�U'} < set(next_agent.wang_list):
					eat_list.append((['4�U', '5�U'], ['3�U', '4�U', '5�U']))          
			elif card == '4�U':
				if {'2�U', '3�U'} < set(next_agent.wang_list):
					eat_list.append((['2�U', '3�U'], ['2�U', '3�U', '4�U']))                     
				if {'3�U', '5�U'} < set(next_agent.wang_list):
					eat_list.append((['3�U', '5�U'], ['3�U', '4�U', '5�U']))                       
				if {'5�U', '6�U'} < set(next_agent.wang_list):
					eat_list.append((['5�U', '6�U'], ['4�U', '5�U', '6�U']))                     
			elif card == '5�U':
				if {'3�U', '4�U'} < set(next_agent.wang_list):
					eat_list.append((['3�U', '4�U'], ['3�U', '4�U', '5�U']))                       
				if {'4�U', '6�U'} < set(next_agent.wang_list):
					eat_list.append((['4�U', '6�U'], ['4�U', '5�U', '6�U']))                       
				if {'6�U', '7�U'} < set(next_agent.wang_list):
					eat_list.append((['6�U', '7�U'], ['5�U', '6�U', '7�U']))                    
			elif card == '6�U':
				if {'4�U', '5�U'} < set(next_agent.wang_list):
					eat_list.append((['4�U', '5�U'], ['4�U', '5�U', '6�U']))                     
				if {'5�U', '7�U'} < set(next_agent.wang_list):
					eat_list.append((['5�U', '7�U'], ['5�U', '6�U', '7�U']))                    
				if {'7�U', '8�U'} < set(next_agent.wang_list):
					eat_list.append((['7�U', '8�U'], ['6�U', '7�U', '8�U']))                       
			elif card == '7�U':
				if {'5�U', '6�U'} < set(next_agent.wang_list):
					eat_list.append((['5�U', '6�U'], ['5�U', '6�U', '7�U']))                      
				if {'6�U', '8�U'} < set(next_agent.wang_list):
					eat_list.append((['6�U', '8�U'], ['6�U', '7�U', '8�U']))                     
				if {'8�U', '9�U'} < set(next_agent.wang_list):
					eat_list.append((['8�U', '9�U'], ['7�U', '8�U', '9�U']))
			if len(eat_list) > 0:
				rtv = next_agent.eat(agent, card, ctype, eat_list)
				
		elif ctype==2:
			if card == '1��' and \
			   ('2��' in next_agent.tube_list) and \
			   ('3��' in next_agent.tube_list):
				eat_list.append((['2��', '3��'], ['1��', '2��', '3��']))
			elif card == '9��' and \
			   ('7��' in next_agent.tube_list) and \
			   ('8��' in next_agent.tube_list):
				eat_list.append((['7��', '8��'], ['7��', '8��', '9��']))                
			elif card == '2��':
				if {'1��', '3��'} < set(next_agent.tube_list):
					eat_list.append((['1��', '3��'], ['1��', '2��', '3��']))
				if {'3��', '4��'} < set(next_agent.tube_list):         
					eat_list.append((['3��', '4��'], ['2��', '3��', '4��']))
			elif card == '8��':
				if {'7��', '9��'} < set(next_agent.tube_list):
					eat_list.append((['7��', '9��'], ['7��', '8��', '9��']))                    
				if {'6��', '7��'} < set(next_agent.tube_list):
					eat_list.append((['6��', '7��'], ['6��', '7��', '8��']))                     
			elif card == '3��':
				if {'1��', '2��'} < set(next_agent.tube_list):
					eat_list.append((['1��', '2��'], ['1��', '2��', '3��']))                     
				if {'2��', '4��'} < set(next_agent.tube_list):
					eat_list.append((['2��', '4��'], ['2��', '3��', '4��'])) 
				if {'4��', '5��'} < set(next_agent.tube_list):
					eat_list.append((['4��', '5��'], ['3��', '4��', '5��']))          
			elif card == '4��':
				if {'2��', '3��'} < set(next_agent.tube_list):
					eat_list.append((['2��', '3��'], ['2��', '3��', '4��']))                     
				if {'3��', '5��'} < set(next_agent.tube_list):
					eat_list.append((['3��', '5��'], ['3��', '4��', '5��']))                       
				if {'5��', '6��'} < set(next_agent.tube_list):
					eat_list.append((['5��', '6��'], ['4��', '5��', '6��']))                     
			elif card == '5��':
				if {'3��', '4��'} < set(next_agent.tube_list):
					eat_list.append((['3��', '4��'], ['3��', '4��', '5��']))                       
				if {'4��', '6��'} < set(next_agent.tube_list):
					eat_list.append((['4��', '6��'], ['4��', '5��', '6��']))                       
				if {'6��', '7��'} < set(next_agent.tube_list):
					eat_list.append((['6��', '7��'], ['5��', '6��', '7��']))                    
			elif card == '6��':
				if {'4��', '5��'} < set(next_agent.tube_list):
					eat_list.append((['4��', '5��'], ['4��', '5��', '6��']))                     
				if {'5��', '7��'} < set(next_agent.tube_list):
					eat_list.append((['5��', '7��'], ['5��', '6��', '7��']))                    
				if {'7��', '8��'} < set(next_agent.tube_list):
					eat_list.append((['7��', '8��'], ['6��', '7��', '8��']))                       
			elif card == '7��':
				if {'5��', '6��'} < set(next_agent.tube_list):
					eat_list.append((['5��', '6��'], ['5��', '6��', '7��']))                      
				if {'6��', '8��'} < set(next_agent.tube_list):
					eat_list.append((['6��', '8��'], ['6��', '7��', '8��']))                     
				if {'8��', '9��'} < set(next_agent.tube_list):
					eat_list.append((['8��', '9��'], ['7��', '8��', '9��']))
			if len(eat_list) > 0:
				rtv = next_agent.eat(agent, card, ctype, eat_list)
			
		elif ctype==3:
			if card == '1��' and \
			   ('2��' in next_agent.bamb_list) and \
			   ('3��' in next_agent.bamb_list):
				eat_list.append((['2��', '3��'], ['1��', '2��', '3��']))
			elif card == '9��' and \
			   ('7��' in next_agent.bamb_list) and \
			   ('8��' in next_agent.bamb_list):
				eat_list.append((['7��', '8��'], ['7��', '8��', '9��']))                
			elif card == '2��':
				if {'1��', '3��'} < set(next_agent.bamb_list):
					eat_list.append((['1��', '3��'], ['1��', '2��', '3��']))
				if {'3��', '4��'} < set(next_agent.bamb_list):         
					eat_list.append((['3��', '4��'], ['2��', '3��', '4��']))
			elif card == '8��':
				if {'7��', '9��'} < set(next_agent.bamb_list):
					eat_list.append((['7��', '9��'], ['7��', '8��', '9��']))                    
				if {'6��', '7��'} < set(next_agent.bamb_list):
					eat_list.append((['6��', '7��'], ['6��', '7��', '8��']))                     
			elif card == '3��':
				if {'1��', '2��'} < set(next_agent.bamb_list):
					eat_list.append((['1��', '2��'], ['1��', '2��', '3��']))                     
				if {'2��', '4��'} < set(next_agent.bamb_list):
					eat_list.append((['2��', '4��'], ['2��', '3��', '4��'])) 
				if {'4��', '5��'} < set(next_agent.bamb_list):
					eat_list.append((['4��', '5��'], ['3��', '4��', '5��']))          
			elif card == '4��':
				if {'2��', '3��'} < set(next_agent.bamb_list):
					eat_list.append((['2��', '3��'], ['2��', '3��', '4��']))                     
				if {'3��', '5��'} < set(next_agent.bamb_list):
					eat_list.append((['3��', '5��'], ['3��', '4��', '5��']))                       
				if {'5��', '6��'} < set(next_agent.bamb_list):
					eat_list.append((['5��', '6��'], ['4��', '5��', '6��']))                     
			elif card == '5��':
				if {'3��', '4��'} < set(next_agent.bamb_list):
					eat_list.append((['3��', '4��'], ['3��', '4��', '5��']))                       
				if {'4��', '6��'} < set(next_agent.bamb_list):
					eat_list.append((['4��', '6��'], ['4��', '5��', '6��']))                       
				if {'6��', '7��'} < set(next_agent.bamb_list):
					eat_list.append((['6��', '7��'], ['5��', '6��', '7��']))                    
			elif card == '6��':
				if {'4��', '5��'} < set(next_agent.bamb_list):
					eat_list.append((['4��', '5��'], ['4��', '5��', '6��']))                     
				if {'5��', '7��'} < set(next_agent.bamb_list):
					eat_list.append((['5��', '7��'], ['5��', '6��', '7��']))                    
				if {'7��', '8��'} < set(next_agent.bamb_list):
					eat_list.append((['7��', '8��'], ['6��', '7��', '8��']))                       
			elif card == '7��':
				if {'5��', '6��'} < set(next_agent.bamb_list):
					eat_list.append((['5��', '6��'], ['5��', '6��', '7��']))                      
				if {'6��', '8��'} < set(next_agent.bamb_list):
					eat_list.append((['6��', '8��'], ['6��', '7��', '8��']))                     
				if {'8��', '9��'} < set(next_agent.bamb_list):
					eat_list.append((['8��', '9��'], ['7��', '8��', '9��']))
			if len(eat_list) > 0:
				rtv = next_agent.eat(agent, card, ctype, eat_list)
		
		if not rtv:
			self.drop_list.append(card)   # ���Y�P,�h�ӵP�i����
			self.play_turn = self.aget_list.index(next_agent)
		else:
			self.disCard(next_agent, rtv) # �Y�P���@�i�P
			#self.play_turn = (self.aget_list.index(next_agent)+1) % len(self.aget_list) # �Y�P�h����U�a
			#self.disCard(next_agent, rtv) 

	# ��P    
	def drawCard(self):
		if self.card_count > 0:
			bb_list = []
			if len(self.bamb_list)>0:
				for i in range(len(self.bamb_list)): bb_list.append(self.bamb_list)
			if len(self.wang_list)>0:
				for i in range(len(self.wang_list)): bb_list.append(self.wang_list)
			if len(self.tube_list)>0:
				for i in range(len(self.tube_list)): bb_list.append(self.tube_list)
			if len(self.flow_list)>0:
				for i in range(len(self.flow_list)): bb_list.append(self.flow_list)                
			if len(self.word_list)>0:
				for i in range(len(self.word_list)): bb_list.append(self.word_list)
			if len(self.wind_list)>0:
				for i in range(len(self.wind_list)): bb_list.append(self.wind_list)
			c_list = bb_list[random.randint(0, len(bb_list)-1)]
			p_idx = random.randint(0, len(c_list)-1)
			self.card_count-=1
			return c_list.pop(p_idx)        

	# �~�P
	def shuffle(self):
		del self.drop_list[:]
		self.win_agent = None
		del self.wind_list[:]
		self.wind_list.append('�F')
		self.wind_list.append('��')
		self.wind_list.append('�n')
		self.wind_list.append('�_')
		self.wind_list = self.wind_list * 4
		self.wind_list.sort()
		del self.word_list[:]
		self.word_list.append('��')
		self.word_list.append('�o')
		self.word_list.append('��')
		self.word_list = self.word_list * 4
		self.word_list.sort()
		del self.flow_list[:]
		self.flow_list.append('�Q')
		self.flow_list.append('��')
		self.flow_list.append('��')
		self.flow_list.append('��')
		self.flow_list.append('�K')
		self.flow_list.append('�L')
		self.flow_list.append('��')
		self.flow_list.append('�V')
		del self.wang_list[:]
		self.wang_list.append('1�U')
		self.wang_list.append('2�U')
		self.wang_list.append('3�U')
		self.wang_list.append('4�U')
		self.wang_list.append('5�U')
		self.wang_list.append('6�U')
		self.wang_list.append('7�U')
		self.wang_list.append('8�U')
		self.wang_list.append('9�U')
		self.wang_list = self.wang_list * 4
		self.wang_list.sort()
		del self.bamb_list[:]
		self.bamb_list.append('1��')
		self.bamb_list.append('2��')
		self.bamb_list.append('3��')
		self.bamb_list.append('4��')
		self.bamb_list.append('5��')
		self.bamb_list.append('6��')
		self.bamb_list.append('7��')
		self.bamb_list.append('8��')
		self.bamb_list.append('9��')
		self.bamb_list = self.bamb_list * 4
		self.bamb_list.sort()
		del self.tube_list[:]
		self.tube_list.append("1��")
		self.tube_list.append("2��")
		self.tube_list.append("3��")
		self.tube_list.append("4��")
		self.tube_list.append("5��")
		self.tube_list.append("6��")
		self.tube_list.append("7��")
		self.tube_list.append("8��")
		self.tube_list.append("9��")
		self.tube_list = self.tube_list * 4
		self.tube_list.sort()
		self.drop_record.clear()
		self.card_count = len(self.wang_list) + len(self.bamb_list) + len(self.tube_list) + \
						  len(self.flow_list) + len(self.word_list) + len(self.wind_list)
		for agent in self.aget_list:
			agent.clean()
			#agent.win = False
			agent.win_card = None            
			del agent.pong_list[:]
			print(agent)

class Agent:
	def __init__(self, name, gb):
		self.win = 0
		self.win_by_draw = 0
		self.lose = 0
		self.name = name
		self.gb = gb
		self.bamb_list = []
		self.wang_list = []
		self.tube_list = []
		self.flow_list = []
		self.word_list = []
		self.wind_list = []
		self.aget_list = []
		self.pong_list = []
		self.card_count = 0
		self.win_card = None
		gb.appendAgent(self)

	# Drop all cards in hand
	def clean(self):
		del self.bamb_list[:]
		del self.wang_list[:]
		del self.tube_list[:]
		del self.flow_list[:]
		del self.word_list[:]
		del self.wind_list[:]
		del self.aget_list[:]
		del self.pong_list[:]
		self.card_count = 0
		
	# ��P
	def draw(self, keep=False):
		card = self.gb.drawCard()
		if GameBoard.GoalState(self, card): # Check goal state
			self.gb.win_agent = self
			self.win_card = card
			self.win_by_draw+=1
			#print("\t[Test] Agent({0}) �ۺN {1}!".format(self.name, card))
			return
		#print("\t[Test] {0} draw {1}...".format(self.name, card))
		ctype = GameBoard.CardType(card)
		if ctype==1:
			self.wang_list.append(card)            
			self.wang_list.sort()
			self.card_count+=1
		elif ctype==2:
			self.tube_list.append(card)
			self.tube_list.sort()
			self.card_count+=1
		elif ctype==3:
			self.bamb_list.append(card)
			self.bamb_list.sort()
			self.card_count+=1
		elif ctype==4:
			self.word_list.append(card)
			self.word_list.sort()
			self.card_count+=1
		elif ctype==5:
			self.wind_list.append(card)
			self.wind_list.sort()
			self.card_count+=1
		else:
			self.flow_list.append(card)
			self.flow_list.sort()
			return self.draw()

		dcard = None
		if not keep:
			dcard = self.drop()
			#print("\t[Test] {0} drop {1}...".format(self.name, dcard))
			#self.gb.disCard(self, dcard)
		return dcard

	# ����W�@�i�P
	def drop(self):
		card = ''
		if len(self.word_list)>0:
			card = self.word_list.pop()
		if (not card) and len(self.wind_list)>0:
			card = self.wind_list.pop()
		if (not card) and len(self.tube_list)>0:
			card = self.tube_list.pop()
		if (not card) and len(self.wang_list)>0:
			card = self.wang_list.pop()
		if (not card) and len(self.bamb_list)>0:
			card = self.bamb_list.pop()
		self.card_count-=1
		return card

	def _pong(self, c_list, count, card):        
		for i in range(count+1):
			self.pong_list.append(card)
			
		for i in range(count):
			c_list.remove(card)
			self.card_count-=1
		
		if count==2:
			dcard = self.drop()
			#print("\t[Test] {0}: Pong '{1}' and drop {2}!".format(self.name, card, dcard))
			#self.gb.disCard(self, dcard)
			return dcard
		else:
			#print("\t[Test] {0}: Gang '{1}'!".format(self.name, card))
			return self.draw(keep=False)
		
	# �I! A callback by GameBoard. Return drop card or redraw card if you want.    
	def pong(self, agent, ctype, count, card):
		if GameBoard.GoalState(self, card): # Check goal state
			self.gb.win_agent = self
			self.win_card = card
			self.win+=1
			agent.close+=1
			#print("\t[Test] Agent({0}) �I�J {1}!!".format(self.name, card))
			return
		
		# Greedy algorithm: Always pong!
		if ctype==1:
			return self._pong(self.wang_list, count, card)                
		elif ctype==2:
			return self._pong(self.tube_list, count, card)                
		elif ctype==3:
			return self._pong(self.bamb_list, count, card)                
		elif ctype==4:
			return self._pong(self.word_list, count, card)                
		elif ctype==5:
			return self._pong(self.wind_list, count, card)
				

	def _eat(self, olist, dlist, elist):
		self.pong_list.extend(elist)
		for e in dlist:
			olist.remove(e)
			self.card_count-=1
		dcard = self.drop()
		#print("\t[Test] {0}: Eat '{1}' and drop {2}!".format(self.name, toCListStr(elist), dcard))
		#self.gb.disCard(self, dcard)
		return dcard

	# �Y�P. Callback by GameBoard
	def eat(self, agent, card, ctype, eat_list):
		if GameBoard.GoalState(self, card): # Check goal state
			self.gb.win_agent = self
			self.win_card = card
			self.win+=1
			agent.lose+=1
			#print("\t[Test] Agent({0}) �Y�J {1}!".format(self.name, card))
			return
		# Greedy algorithm: Always eat from the first choice
		if ctype==1:
			return self._eat(self.wang_list, eat_list[0][0], eat_list[0][1])
		elif ctype==2:
			return self._eat(self.tube_list, eat_list[0][0], eat_list[0][1])
		elif ctype==3:
			return self._eat(self.bamb_list, eat_list[0][0], eat_list[0][1])

	# �N�P��J
	def _feedCard(self, card):
		ctype = GameBoard.CardType(card)
		if ctype==1:
			self.wang_list.append(card)
			self.wang_list.sort()
			self.card_count+=1
			return True
		elif ctype==2:
			self.tube_list.append(card)
			self.tube_list.sort()
			self.card_count+=1
			return True
		elif ctype==3:
			self.bamb_list.append(card)
			self.bamb_list.sort()
			self.card_count+=1
			return True
		elif ctype==4:
			self.word_list.append(card)
			self.word_list.sort()
			self.card_count+=1
			return True
		elif ctype==5:
			self.wind_list.append(card)
			self.wind_list.sort()
			self.card_count+=1
			return True
		else:
			self.flow_list.append(card)
			self.flow_list.sort()

	def handleGang(self):
		drawFlag = False
		if len(self.wang_list)>3:
			for e in set(self.wang_list):
				if self.wang_list.count(e)==4:
					self.pong_list.extend([e]*4)
					while e in self.wang_list:
						self.wang_list.remove(e)
						self.card_count-=1
					while not self._feedCard(self.gb.drawCard()):
						pass # �����줣�O��P
					self.wang_list.sort()
					drawFlag=True
		if len(self.tube_list)>3:
			for e in set(self.tube_list):
				if self.tube_list.count(e)==4:
					self.pong_list.extend([e]*4)
					while e in self.tube_list:
						self.tube_list.remove(e)
						self.card_count-=1
					while not self._feedCard(self.gb.drawCard()):
						pass # �����줣�O��P
					self.tube_list.sort()
					drawFlag=True
		if len(self.bamb_list)>3:
			for e in set(self.bamb_list):
				if self.bamb_list.count(e)==4:
					self.pong_list.extend([e]*4)
					while e in self.bamb_list:
						self.bamb_list.remove(e)
						self.card_count-=1
					while not self._feedCard(self.gb.drawCard()):
						pass # �����줣�O��P
					self.bamb_list.sort()
					drawFlag=True
		if len(self.word_list)>3:
			for e in set(self.word_list):
				if self.word_list.count(e)==4:
					self.pong_list.extend([e]*4)
					while e in self.word_list:
						self.word_list.remove(e)
						self.card_count-=1
					while not self._feedCard(self.gb.drawCard()):
						pass # �����줣�O��P
					self.word_list.sort()
					drawFlag=True
		if len(self.wind_list)>3:
			for e in set(self.wind_list):
				if self.wind_list.count(e)==4:
					self.pong_list.extend([e]*4)
					while e in self.wind_list:
						self.wind_list.remove(e)
						self.card_count-=1
					while not self._feedCard(self.gb.drawCard()):
						pass # �����줣�O��P
					self.wind_list.sort()
					drawFlag=True
		if drawFlag:
			self.handleGang()
			
	# �o�P        
	def assignCard(self):
		# �⺡ 16 �i�P(������P)
		while self.card_count < 16:
			card = self.gb.drawCard()
			self._feedCard(card)
				
		# �B�z�b�P
		self.handleGang()
					
			
	def __str__(self):
		self_str = "{0}({1}/{2}/{3}): [".format(self.name, self.win_by_draw, self.win, self.lose)
		for card in self.wang_list:
			self_str+="{0} ".format(card)
		for card in self.tube_list:
			self_str+="{0} ".format(card)
		for card in self.bamb_list:
			self_str+="{0} ".format(card)
		for card in self.word_list:
			self_str+="{0} ".format(card)
		for card in self.wind_list:
			self_str+="{0} ".format(card)    
		self_str = "{0}]".format(self_str)
		if len(self.flow_list) > 0:
			self_str+=" / [ "
			for card in self.flow_list:
				self_str+="{0} ".format(card)
			self_str+="]"
		else:
			self_str+=" / []"
		if len(self.pong_list) > 0:
			self_str+=" / [ "
			for card in self.pong_list:
				self_str+="{0} ".format(card)
			self_str+="]"
		else:
			self_str+=" / []"
		if self.win_card:
			self_str+=" -> {0}".format(self.win_card)
		return self_str           


# 2) Testing code
##gb = GameBoard()
##agent1 = Agent('Robot1', gb)
##agent2 = Agent('Robot2', gb)
##agent3 = Agent('Robot3', gb)
##agent4 = Agent('Self', gb)
##for i in range(50):
##    print("\t[Info] Play!")
##    gb.play()
##    print("\t[Info] ����={0}".format(gb.drop_list))
##    print("\t[Info] Drop record:\n{0}".format(gb.drop_record))
##    print("\t[Info] Wash board")

