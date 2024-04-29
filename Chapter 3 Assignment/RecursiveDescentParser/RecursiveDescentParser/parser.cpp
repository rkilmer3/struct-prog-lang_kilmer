/*
parser.cpp
This program takes a given EBNF structure
Reads from a file
And tells us whether or not something is a valid expression in the grammar
*/
#include<iostream> 
#include<string>
#include<fstream>
#include<cctype>
#include<vector>
using std::string; using std::cout; using std::ifstream; using std::vector;

/*
EBNF Grammar
<expr> = <expr> + <expr>
<expr> = <expr> * <expr>
<expr> = -<expr>
<expr> = <integer>
<integer> = Positive real numbers
*/

int parseExpression(char& token)
{
	switch (token)
	{
	case '+':
		return 1;
		break;
	case '*':
		return 1;
		break;
	case '-':
		return 4;
		break;
	}
	return parseInteger(token);
}

int parseInteger(char& token)
{
	if (std::isalpha(token))
	{
		return 3;
	}
	else 
	{
		return 2;
	}
}

vector<int> parser(string& tokens)
{
	vector<int> parsedTokens;
	for (int i = 0; i < tokens.length(); ++i)
	{
		parsedTokens.push_back(parseExpression(tokens[i]));
	}
	return parsedTokens;
}

int main(int argc, char* argv[])
{
	ifstream fin;
	fin.open(argv[0]);
	string readTokens;
	if (!fin.is_open())
	{
		std::cerr << "Could not open file";
	}

	while (std::getline(fin, readTokens))
	{
		int previousToken = 0;
		bool flag = false;
		vector<int> parsedExpression = parser(readTokens);
		for (int i = 0; i < parsedExpression.size(); ++i)
		{
			if (i > 0)
			{
				previousToken = parsedExpression[i - 1];
			}
			if (i == 0 && parsedExpression[i] == 1)
			{
				cout << readTokens + " is not an expression" << std::endl;
				flag = true;
			}
			if (previousToken == 1 && parsedExpression[i] == 1 && !flag)
			{
				cout << readTokens + " is not an expression" << std::endl;
				flag = true;
			}
			if (parsedExpression[i] == 3 && !flag)
			{
				cout << readTokens + " contains a letter and is not an expression" << std::endl;
				flag = true;
			}
		}
		if (!flag)
		{
			cout << readTokens + " is an expression" << std::endl;
		}
	}

	fin.close();

	return 0;
}
