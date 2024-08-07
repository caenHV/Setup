# <p style="text-align: center;"><b>Tickets package</b></p>

## **TicketMaster**

Является основным инструментом общения с HV инфраструктурой ДК КМД-3.

### * **TicketMaster.serialize(ticket: Type[Ticket])->str:**

Этот метод позволяет получить json представление соответствующего Ticket'а.

### * **TicketMaster.deserialize(cls, json_string: str)->Ticket:**

Данный метод является по факту factory методом. На выходе получается объект, соответствующего наследника класса Ticket согласно полям в json_string.
У json_string в минимальном виде (то есть все поля сверх указанного в расчёт не берутся) должна быть следующая структура:
```
{
    "name" : *ticket_name*,
    "params" : {
        "*param_name_1*" : *param_value_1*,
        ...
        "*param_name_N*" : *param_value_N*
    }
}
```

<u>**Важно!!!**</u><br/>
В данном методе не проверяется правильность как форматирования самого json_string, так и разумность значений, указанных в нём. В связи с этим перед использованием этого метода необходимо удостовериться в качестве json_string при помощи метода ***TicketMaster.inspect***.

### * **TicketMaster.inspect(json_string: str, ticket_type: TicketType)->bool:**

Проверяет качество форматирования json_string согласно требуемому в ***TicketMaster.deserialize***, а также проверяет соответствие указанных параметров требованиям соответствующего Ticket'а.

В случае нахождения какого-либо несоответствия выбрасывается исключение с описанием найденного. Если всё хорошо, то на выход идёт True.
___

## **Tickets и TicketType** 
**Tickets** это пакет со всеми имеющимися Ticket'ами.

**TicketType** это enum, где имена членов -- название тикета, а значение -- соответствующий наследник класса **Ticket**. 

У всех наследников **Ticket** одинаковый интерфейс:
* **init(self, params: dict)**:
Создаёт тикет с параметрами = params (словарь из вышеописанного json_string).
* **execute(self, handler: Handler)->str**:
Выполняет тикет с помощью указанного хендлера сетапа и возвращает json строку в следующем формате:
```
{
    "status": bool,
    "body" : {
        "error" : str(e) <- in case if status == False
        ... 
    }
}
```
* classmethod **type_description: Ticket_Type_info**:
Возвращает описание данного типа тикетов в формате датакласса, у которого есть проперти json (возвращает json строку; её формат будет описан далее).
* **description: Ticket_info**:
Возвращает описание данного тикетов в формате датакласса, у которого есть проперти json (возвращает json строку; её формат будет описан далее).

### **Ticket_Type_info**
Датакласс, характеризующий определённый тип тикетов, со следующими полями:
* **name**: str --  Название Тикета.
* **args**: dict[str, dict[str, Any]] -- Описание принимаемых параметров словарь пар 
```
args -- словарь пар {arg_name: str, arg_info: dict}; у arg_info является dict["*parameter_name*" : list[*parameter_min_val*, *parameter_max_val*, "*parameter_description*"]]
```

И проперти **Ticket_Type_info.json**, возвращающей объект в виде json строки.

### **Ticket_info**
Датакласс, характеризующий конкретный тикет, со следующими полями:
* **name**: str --  Название Тикета.
* **args**: dict[str, dict[str, Any]] -- Описание принимаемых параметров (словарь пар **{arg_name: str, arg_info: dict[par_name: str, par_val: Any]}**)

И проперти **Ticket_info.json**, возвращающей объект в виде json строки.

---
### **Down**
Сбрасывает напряжение на всех слоях. Никакие параметры не требуются. После выполнения не возвращает дополнительных параметров.

### **SetVoltage**
Устанавливает напряжение согласно множителю <u>**target_voltage**</u> (**volt = target_voltage * default_voltage**), которое задаётся в параметрах.
**default_voltage** задаётся в конфиге **Handler**-а.
После выполнения не возвращает дополнительных параметров.

### **GetParams**
Считывает параметры всех активных каналов. После выполнения возвращает в *body* элемент с ключом *params* и значением (значения параметров каналов) в формате
```
{
    "*board_address*_*conet*_*link*_*channel_num*" : {
        "*param_name_1*" : *param_value(float | int | datetime | None)*
        ...
        "*param_name_N*" : *param_value*
    }
}
```
