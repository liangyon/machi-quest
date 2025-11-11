// map to refer to  
# VPC (10.0.0.0/16)
# │
# ├─ Public Subnet 1 (10.0.1.0/24) [us-east-1a]
# │  ├─ Route: 0.0.0.0/0 → Internet Gateway
# │  └─ Contains: NAT Gateway 1, ALB
# │
# ├─ Public Subnet 2 (10.0.2.0/24) [us-east-1b]
# │  ├─ Route: 0.0.0.0/0 → Internet Gateway
# │  └─ Contains: NAT Gateway 2, ALB
# │
# ├─ Private Subnet 1 (10.0.11.0/24) [us-east-1a]
# │  ├─ Route: 0.0.0.0/0 → NAT Gateway 1
# │  └─ Contains: Backend containers, Worker containers
# │
# ├─ Private Subnet 2 (10.0.12.0/24) [us-east-1b]
# │  ├─ Route: 0.0.0.0/0 → NAT Gateway 2
# │  └─ Contains: Backend containers, Worker containers
# │
# ├─ Database Subnet 1 (10.0.21.0/24) [us-east-1a]
# │  ├─ Route: 0.0.0.0/0 → NAT Gateway 1
# │  └─ Contains: RDS primary
# │
# └─ Database Subnet 2 (10.0.22.0/24) [us-east-1b]
#    ├─ Route: 0.0.0.0/0 → NAT Gateway 2
#    └─ Contains: RDS standby, ElastiCache


// create vpc
resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr

  enable_dns_hostnames = true
  enable_dns_support   = true

  tags = merge(
    {
      "Name" = "${var.environment}-${var.project_name}-vpc"
    },
    var.tags
  )
}
//create internet gateway
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-igw"
    }
  )
}

//public subnet 1 and 2 in two availability zones
resource "aws_subnet" "public_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.1.0/24"
  availability_zone = var.availability_zones[0]

  # Resources in this subnet get public IPs automatically
  map_public_ip_on_launch = true

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-public-subnet-1"
      Type = "Public"
    }
  )
}
resource "aws_subnet" "public_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.2.0/24"
  availability_zone = var.availability_zones[1]

  map_public_ip_on_launch = true

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-public-subnet-2"
      Type = "Public"
    }
  )
}


//private subnet 1 and 2 for my containers
resource "aws_subnet" "private_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.11.0/24"
  availability_zone = var.availability_zones[0]

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-private-subnet-1"
      Type = "Private"
    }
  )
}
resource "aws_subnet" "private_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.12.0/24"
  availability_zone = var.availability_zones[1]

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-private-subnet-2"
      Type = "Private"
    }
  )
}

//database subnet 1 and 2 for rds
resource "aws_subnet" "database_1" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.21.0/24"            # 256 IPs
  availability_zone = var.availability_zones[0] # us-east-1a

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-database-subnet-1"
      Type = "Database"
    }
  )
}
resource "aws_subnet" "database_2" {
  vpc_id            = aws_vpc.main.id
  cidr_block        = "10.0.22.0/24"            # 256 IPs
  availability_zone = var.availability_zones[1] # us-east-1b

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-database-subnet-2"
      Type = "Database"
    }
  )
}


//elastic ips for nat gateways
//eip is static public ip addr, are basically free
resource "aws_eip" "nat_1" {
  domain     = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-nat-eip-1"
    }
  )
}

resource "aws_eip" "nat_2" {
  domain     = "vpc"
  depends_on = [aws_internet_gateway.main]

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-nat-eip-2"
    }
  )
}


//nat gateways in public subnets
resource "aws_nat_gateway" "nat_1" {
  allocation_id = aws_eip.nat_1.id
  subnet_id     = aws_subnet.public_1.id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-nat-gateway-1"
    }
  )
  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "nat_2" {
  allocation_id = aws_eip.nat_2.id
  subnet_id     = aws_subnet.public_2.id

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-nat-gateway-2"
    }
  )
  depends_on = [aws_internet_gateway.main]
}


//route table for public subnets
resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"                  //allow the whole internet
    gateway_id = aws_internet_gateway.main.id //route to internet gateway
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-public-rt"
    }
  )
}
//associate public subnets with public route table
resource "aws_route_table_association" "public_1" {
  subnet_id      = aws_subnet.public_1.id
  route_table_id = aws_route_table.public.id
}
resource "aws_route_table_association" "public_2" {
  subnet_id      = aws_subnet.public_2.id
  route_table_id = aws_route_table.public.id
}

//route table for private subnets
resource "aws_route_table" "private_1" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0" //allow the whole internet for now
    nat_gateway_id = aws_nat_gateway.nat_1.id
  }
  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-private-rt-1"
    }
  )
}
resource "aws_route_table" "private_2" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0" //allow the whole internet for now
    nat_gateway_id = aws_nat_gateway.nat_2.id
  }
  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-private-rt-2"
    }
  )
}
//associate private subnets with private route tables
resource "aws_route_table_association" "private_1" {
  subnet_id      = aws_subnet.private_1.id
  route_table_id = aws_route_table.private_1.id
}
resource "aws_route_table_association" "private_2" {
  subnet_id      = aws_subnet.private_2.id
  route_table_id = aws_route_table.private_2.id
}

//db route table 1 and 2
resource "aws_route_table" "database_1" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0" //allow the whole internet for now
    nat_gateway_id = aws_nat_gateway.nat_1.id
  }
  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-database-rt"
    }
  )
}
resource "aws_route_table" "database_2" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0" //allow the whole internet for now, security groups will block unwanted traffic
    nat_gateway_id = aws_nat_gateway.nat_2.id
  }
  tags = merge(
    var.tags,
    {
      Name = "${var.environment}-${var.project_name}-database-rt-2"
    }
  )
}
//associate db subnets with db route tables
resource "aws_route_table_association" "database_1" {
  subnet_id      = aws_subnet.database_1.id
  route_table_id = aws_route_table.database_1.id
}
resource "aws_route_table_association" "database_2" {
  subnet_id      = aws_subnet.database_2.id
  route_table_id = aws_route_table.database_2.id
}

