from __future__ import annotations
from dataclasses import dataclass
from typing import Union, Optional
import string

from rules_doc_generator.model.text import (RefDict, RefInfo, FormatText, Example)

@dataclass
class Rule:
  id: str
  formatText: FormatText
  section: bool
  rules: list[Rule]
  examples: list[Example]

  def to_html(self, id_map: RefDict) -> str:
    result = self.formatText.to_html(id_map)
    for example in self.examples:
      result += f'<p>{example.to_html(id_map)}</p>'
    if self.rules:
      result += '<ol>'
      for rule in self.rules:
        result += f'<li class="SubRule" id="{id_map[rule.id].reference}">{rule.to_html(id_map)}</li>'
      result += '</ol>'
    return result

  def to_latex(self, id_map: RefDict) -> str:
    result = self.formatText.to_latex(id_map)
    result += '\n'
    for example in self.examples:
      result += f'\\0 {example.to_latex(id_map)}\n'
    if self.rules:
      for rule in self.rules:
        result += f'\\2 {rule.to_latex(id_map)}'
    return result

  def id_map_sub_rules(self, ctx: str, i: int, dict: dict[int, str]) -> int:
    if self.id in dict:
      raise Exception(f'id defined twice: {self.id}')
    letters = string.ascii_lowercase[:14]
    dict[self.id] = RefInfo(f'{ctx}{letters[i]}', 'rule', '', self.id)

  def id_map(self, ctx: str, i: int, dict: dict[int, str]) -> int:
    if self.id in dict:
      raise Exception(f'id defined twice: {self.id}')
    dict[self.id] = RefInfo(f'{ctx}.{i}', 'rule', '', self.id)
    for j, rule in enumerate(self.rules):
      rule.id_map_sub_rules(f'{ctx}.{i}', j, dict)

@dataclass
class Section:
  id: str
  text: str
  snippet: Optional[FormatText]
  rules: list[Rule]

  def to_html(self, id_map: RefDict) -> str:
    result = f'<h2>{self.text}</h2>'
    if self.snippet:
      result += f'<p>{self.snippet.to_html(id_map)}</p>'
    result += '<ol>'
    for elem in self.rules:
      result += f'<li class="Rule" id="{id_map[elem.id].reference}">{elem.to_html(id_map)}</li>'
    result += '</ol>'
    return result

  def to_latex(self, id_map: RefDict) -> str:
    result = f'\subsection{{{self.text}}}\n'
    result += f'\label{{{self.id}}}\n'
    if self.snippet:
      result += f'{self.snippet.to_latex(id_map)}\n'
    prefix = id_map[self.id].reference
    result += '\\begin{outline}[enumerate]\n'
    for elem in self.rules:
      match elem:
        case Rule(): 
          if elem.section:
            result += '\\addtocounter{subsubsection}{1}\n'
            result += '\\addcontentsline{toc}{subsubsection}{\\arabic{section}.\\arabic{subsection}.\\arabic{subsubsection}~~ ' + elem.formatText.to_latex(id_map) + '}\n'
            result += f'\\refstepcounter{{rule_section}}\label{{{elem.id}}}'
          result += f'\\1 {elem.to_latex(id_map)}\n'
        case Example(): result += f'\\0 \begin{{adjustwidth}}{{37pt}}{{0pt}} {elem.to_latex(id_map)} \end{{adjustwidth}}\n'
    result += '\end{outline}\n'
    return result

  def id_map(self, ctx: str, i: int, dict: dict[int, str]):
    if self.id in dict:
      raise Exception(f'id defined twice: {self.id}')
    dict[self.id] = RefInfo(f'{ctx}.{i}', 'section', self.text, self.id)
    for j, elem in enumerate(self.rules):
      elem.id_map(f'{ctx}.{i}', j + 1, dict)

@dataclass
class Header:
  id: str
  text: str
  sections: list[Section]

  def to_html(self, id_map: RefDict) -> str:
    result = f'<h1>{self.text}</h1><ol>'
    for section in self.sections:
      result += f'<li class="Section" id="{id_map[section.id].reference}">{section.to_html(id_map)}</li>'
    result += '</ol>'
    return result

  def to_latex(self, id_map: RefDict) -> str:
    result = f'\section{{{self.text}}}\n'
    for section in self.sections:
      result += section.to_latex(id_map)
    return result

  def id_map(self, i: int, dict: RefDict):
    if self.id in dict:
      raise Exception(f'id defined twice: {self.id}', self.text)
    dict[self.id] = RefInfo(f'{i}', 'header', self.text, self.id)
    for j, elem in enumerate(self.sections):
      elem.id_map(f'{i}', j + 1, dict)

@dataclass
class Document:
  headers: list[Section]

  def to_html(self, id_map: RefDict) -> str:
    result = '<ol>'
    for header in self.headers:
      result += f'<li class="Header" id="{id_map[header.id].reference}">{header.to_html(id_map)}</li>'
    result += '</ol>'
    return result

  def to_latex(self, id_map: RefDict) -> str:
    latex_template = open("templates/latex/template.tex", "r")
    latex_content = latex_template.read()
    latex_template.close()
    
    latex_content = latex_content.replace("__CHANGELOG_PLACEHOLDER__", "")

    document_content = ''
    for element in self.headers:
      document_content += element.to_latex(id_map)
    latex_content = latex_content.replace("__DOCUMENT_PLACEHOLDER__", document_content)

    return latex_content

  def id_map(self):
    id_map = {}
    for j, elem in enumerate(self.headers):
      elem.id_map(j + 1, id_map)
    return id_map
