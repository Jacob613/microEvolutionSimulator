import random
import math
import sys
import pygame
from pygame.locals import *

pygame.init()

# please ensure pygame is installed before attempting to run; requires atleast python 3.10 to run

# the rate of mutation is 1 / mutation_chance
MUTATION_CHANCE = 500
MATING_ENERGY_THRESHOLD = 1500
BASE_ENERGY_LEVEL = 1000

# splits a string into a list, with each item containing 3 characters
def splitIntoCodons(strand):
    return [(strand[i:i+3]) for i in range(0, len(strand), 3)]

# checks if modifying an x or y coordinate would put it outside of the bounds of the map
def inBounds(coord, vel):
    if coord + vel > 1000 or coord + vel < 0:
        return False
    return True


class Cell:
    def __init__(self, x, y, energyLevel, DNA):
        self.x = x        
        self.y = y
        self.energyLevel = energyLevel
        self.size = 0
        self.direction = 0
        self.spasmRate = 0
        self.DNA = DNA
        self.dead = False
        
    def transcription(self):
        RNA = ""
        for c in self.DNA:
            match c:
                case 'A':
                    RNA += 'U'
                case 'T':
                    RNA += 'A'
                case 'C':
                    RNA += 'G'
                case 'G':
                    RNA += 'C'
        return RNA
    
    def translation(self, mRNA):
        geneValue = 0
        geneIncrement = 0 #used to determine which gene the geneValue is currently being calculated for; incremented at every 'AAA' codon
        mRNA = splitIntoCodons(mRNA)
        
        for codon in mRNA:
            if codon == 'AAA': #start/stop codon
                match geneIncrement:
                    case 1:
                        self.size += geneValue
                    case 2:
                        self.direction += geneValue
                    case 3:
                        self.spasmRate += geneValue
                        
                geneValue = 0
                geneIncrement += 1
                continue # if codon is a start codon: set the variable which the geneValue has been calculated for; increment to the next gene
            else:
                for c in codon:
                    match c:
                        case 'A':
                            pass
                        case 'U':
                            geneValue += 10
                        case 'C':
                            geneValue += 50
                        case 'G':
                            geneValue += 100

    # sets the variables of the cell
    def birth(self):
        self.translation(self.transcription())
        
    
    def move(self):
        if inBounds(self.x, math.cos(self.direction)):
            self.x += math.cos(self.direction)
            self.energyLevel -= 1
        if inBounds(self.y, math.sin(self.direction)):
            self.y += math.sin(self.direction)
            self.energyLevel -= 1
        
        if random.random() < (self.spasmRate / 100): # probability that cell gets to spasm, i.e make another move in a random direction
            xDir = random.randint(0, 360)
            yDir = random.randint(0, 360)
            
            if inBounds(self.x, math.cos(xDir)):
                self.x += math.cos(xDir)
                self.energyLevel -= 1
                
            if inBounds(self.y, math.sin(yDir)):
                self.y += math.sin(yDir)
                self.energyLevel -= 1


class Food():
    def __init__(self, x, y, value):
        self.x = x
        self.y = y
        self.value = value
        
    




def mate(cellA, cellB, energy):
    DNAstrandA = splitIntoCodons(cellA.DNA)
    DNAstrandB = splitIntoCodons(cellB.DNA)
    newStrand = ""
    
    if len(DNAstrandA) >= len(DNAstrandB):
        longerStrand = DNAstrandA
        shorterStrand = DNAstrandB
    else:
        longerStrand = DNAstrandB
        shorterStrand = DNAstrandA

    # the first segment will be somewhere between 0 and the the middle of the shorter strand
    
    splitPointA = random.randint(1, math.ceil(len(shorterStrand)/2))
    
    # the second segment will be somewhere between the middle and end of the shorter strand
    
    splitPointB = random.randint(splitPointA + 1, len(shorterStrand))
    
    # decides which parent will provide DNA for the first section
    if random.randint(1,2) == 1:
        for i in range(0, splitPointA):
            newStrand += longerStrand[i]
    else:
        for i in range(0, splitPointA):
            newStrand += shorterStrand[i]

    # decides which parent will provide DNA for the second section
    if random.randint(1,2) == 1:
        for i in range(splitPointA, splitPointB):
            newStrand += longerStrand[i]
    else:
        for i in range(splitPointA, splitPointB):
            newStrand += shorterStrand[i]

    # decides which parent will provide DNA for the final section
    if random.randint(1,2) == 1:
        for i in range(splitPointB, len(shorterStrand)):
            newStrand += longerStrand[i]
    else:
        for i in range(splitPointB, len(shorterStrand)):
            newStrand += shorterStrand[i]

    # any left over DNA from the longer stand will be added to end of the new strand
    for i in range(len(shorterStrand), len(longerStrand)):
        newStrand += longerStrand[i]
    
    for i in range(len(newStrand)):
        if random.randint(1, MUTATION_CHANCE) == 1:
            print("mutation")
            x = random.randint(1,4)
            match x:
                case 1:
                    newStrand = newStrand[:i] + 'A' + newStrand[i + 1:] # strings are immutable in python, this replaces the old string with a new modified string
                case 2:
                    newStrand = newStrand[:i] + 'T' + newStrand[i + 1:]
                case 3:
                    newStrand = newStrand[:i] + 'C' + newStrand[i + 1:]
                case 4: 
                    newStrand = newStrand[:i] + 'G' + newStrand[i + 1:]

    
    newCell = Cell(cellA.x, cellA.y, energy, newStrand)
    newCell.birth()
    return newCell




def inContactWithCell(target, container):
    for i in range(len(container)):
        if target != container[i]:
            if target.x >= container[i].x and target.x <= container[i].x + container[i].size:
                if target.y >= container[i].y and target.y <= container[i].y + container[i].size:
                    return i
            if container[i].x >= target.x and container[i].x <= target.x + target.size:
                if container[i].y >= target.y and container[i].y <= target.y + target.size:
                    return i
    return -1


# checks if the cell is in contact with food or if the food is in contact with the cell
def inContactWithFood(target, container, foodSize):
    for i in range(len(container)):
        if container[i].x >= target.x and container[i].x <= target.x + target.size:
            if container[i].y >= target.y and container[i].y <= target.y + target.size:
                return i
        if target.x >= container[i].x and target.x <= container[i].x + foodSize:
            if target.y >= container[i].y and target.y <= container[i].y + foodSize:
                return i
    return -1


def spawnFood():
    for i in range(int(foodAmount)):
        match foodBias:
            case "none":
                foodHolder.append(Food(random.randint(0, 1000), random.randint(0, 1000), 50))
            case "left":
                foodHolder.append(Food(random.randint(0, 300), random.randint(0, 1000), 50))
            case "right":
                foodHolder.append(Food(random.randint(700, 1000), random.randint(0, 1000), 50))
            case "up":
                foodHolder.append(Food(random.randint(0, 1000), random.randint(0, 100), 50))
            case "down":
                foodHolder.append(Food(random.randint(0, 1000), random.randint(700, 1000), 50))

DISPLAY=pygame.display.set_mode((1000,1000),0,32)

WHITE=(255,255,255)
BLUE=(0,0,255)
RED=(255,0,0)


DISPLAY.fill(WHITE)

pygame.draw.rect(DISPLAY,BLUE,(200,150,100,50))
    
cycleCounter = 0
cycleSpeed = 100 # the amount of frames in between each cycle

# A regeneration is when the program takes all the alive cells and puts them in the middle, and also regenrates the food
# This is to really help demonstrate which phenotype is dominant
regenerationCounter = 0
regenerationSpeed = 300 # the amount of cycles in between each regeneration

populationSize = input("Enter population size: ")

foodAmount = input("How much food should there be: ")

foodBias = input("Bias of food spawning location(none, left, right, up, down): ")

cellHolder = []
foodHolder = []

spawnFood()

# randomly generates n cells with one of four genotypes
for i in range(int(populationSize)):
    x = random.randint(1, 4)
    match x:
        # genes: size-direction-spasmRate
        case 1:
            cellHolder.append(Cell(500, 500, BASE_ENERGY_LEVEL, "TTTAAATTTCTTTTTCCCTTT"))
        case 2:
            cellHolder.append(Cell(500, 500, BASE_ENERGY_LEVEL, "TTTAAATTTCCTTTTGTTTTT"))
        case 3:
            cellHolder.append(Cell(500, 500, BASE_ENERGY_LEVEL, "TTTAAATTTCCCTTTGTTTTT"))
        case 4:
            cellHolder.append(Cell(500, 500, BASE_ENERGY_LEVEL, "TTTAAATTTATTTTTGTTTTT"))

for i in range(len(cellHolder)):
    cellHolder[i].birth()
               

run = True
while run:
    if cycleCounter >= cycleSpeed:
        numberOfCellsAlive = 0
        for c in cellHolder:
            if not c.dead:
                numberOfCellsAlive += 1
        if numberOfCellsAlive == 0:
            run = False
            break
        #print(numberOfCellsAlive)
        for i in range(len(cellHolder)):
            if not cellHolder[i].dead:
                # Is out of energy? -> become dead
                if cellHolder[i].energyLevel <= 0:
                    cellHolder[i].dead = True
                    #print("cell died")
                    continue
                # move every frame
                cellHolder[i].move()
                # In contact with food? -> gain energy, delete food from world
                foodContactIndex = inContactWithFood(cellHolder[i], foodHolder, 20)
                if foodContactIndex != -1:
                    cellHolder[i].energyLevel += foodHolder[foodContactIndex].value
                    del foodHolder[foodContactIndex]
                    #print("Food eaten")

                # In contact with cell? -> if both cells are at correct energy level, expend energy and mate
                cellContactIndex = inContactWithCell(cellHolder[i], cellHolder)
                if cellContactIndex != -1:
                    if cellHolder[i].energyLevel > MATING_ENERGY_THRESHOLD and cellHolder[cellContactIndex].energyLevel > MATING_ENERGY_THRESHOLD:
                        cellHolder[i].energyLevel -= BASE_ENERGY_LEVEL / 2
                        cellHolder[cellContactIndex].energyLevel -= BASE_ENERGY_LEVEL / 2
                        #print("cells mated")
                        cellHolder.append(mate(cellHolder[i], cellHolder[cellContactIndex], BASE_ENERGY_LEVEL))
        cycleCounter = 0

        regenerationCounter += 1
        print(regenerationCounter)
        if regenerationCounter >= regenerationSpeed:
            for i in range(len(cellHolder)):
                foodHolder.clear()
                cellHolder[i].x = 500
                cellHolder[i].y = 500
                spawnFood()
                regenerationCounter = 0
                print("regenerated")

        
        ####graphics####

        for event in pygame.event.get():
            if event.type==QUIT:
                pygame.quit()
                sys.exit()
        DISPLAY.fill(WHITE)
        for f in foodHolder:
            pygame.draw.rect(DISPLAY,RED,(f.x, f.y , 20, 20))
        for c in cellHolder:
            if not c.dead:
                pygame.draw.rect(DISPLAY,BLUE,(c.x, c.y , c.size, c.size))

        pygame.display.update()
        
    else:
        cycleCounter += 1
