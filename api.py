import json
from http.server import BaseHTTPRequestHandler, HTTPServer
import mysql.connector
from datetime import date, datetime
from decimal import Decimal

# Database Configuration
DB_CONFIG = {
    "host": "localhost",
    "user": "root",
    "password": "123456789",
    "database": "gym_management"
}


def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, (date, datetime)):
            return obj.isoformat()
        if isinstance(obj, Decimal):
            return float(obj)
        return super().default(obj)

class RequestHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            with get_db_connection() as conn:
                with conn.cursor(dictionary=True) as cursor:
                    if self.path == "/members":
                        # Fetch all members
                        cursor.execute("SELECT * FROM members")
                        result = cursor.fetchall()
                    elif self.path.startswith("/attendance/"):
                        # Fetch attendance for a member
                        member_id = self.path.split("/")[-1]
                        cursor.execute("SELECT * FROM attendance WHERE member_id = %s", (member_id,))
                        result = cursor.fetchall()
                    else:
                        self.send_error(404, "Invalid endpoint")
                        return

            response_body = json.dumps(result, cls=CustomJSONEncoder)
            self.send_response(200)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(response_body.encode())
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

    def do_POST(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            with get_db_connection() as conn:
                with conn.cursor() as cursor:
                    if self.path == "/add_member":
                        # Add a new member
                        cursor.execute("""
                            INSERT INTO members (name, contact, email, join_date, membership_plan, payment_status)
                            VALUES (%s, %s, %s, NOW(), %s, %s)
                        """, (data['name'], data['contact'], data['email'], data['membership_plan'], data['payment_status']))
                        conn.commit()
                        response = {"message": "Member added successfully"}
                    elif self.path == "/add_attendance":
                        # Add attendance
                        cursor.execute("""
                            INSERT INTO attendance (member_id, check_in_date, check_out_date)
                            VALUES (%s, %s, %s)
                        """, (data['member_id'], data['check_in_date'], data['check_out_date']))
                        conn.commit()
                        response = {"message": "Attendance added successfully"}
                    else:
                        self.send_error(404, "Invalid endpoint")
                        return

        
            self.send_response(201)
            self.send_header("Content-type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

    def do_PUT(self):
        try:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data.decode('utf-8'))

            if self.path.startswith("/update_payment/"):
                member_id = self.path.split("/")[-1]
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("""
                            UPDATE members SET payment_status = %s WHERE member_id = %s
                        """, (data['payment_status'], member_id))
                        conn.commit()

              
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"message": "Payment status updated successfully"}
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_error(404, "Invalid endpoint")
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")

    def do_DELETE(self):
        try:
            if self.path.startswith("/delete_member/"):
                member_id = self.path.split("/")[-1]
                with get_db_connection() as conn:
                    with conn.cursor() as cursor:
                        cursor.execute("DELETE FROM members WHERE member_id = %s", (member_id,))
                        conn.commit()

              
                self.send_response(200)
                self.send_header("Content-type", "application/json")
                self.end_headers()
                response = {"message": "Member deleted successfully"}
                self.wfile.write(json.dumps(response).encode())
            else:
                self.send_error(404, "Invalid endpoint")
        except Exception as e:
            self.send_error(500, f"Server error: {str(e)}")


def run(server_class=HTTPServer, handler_class=RequestHandler, port=8080):
    server_address = ("", port)
    httpd = server_class(server_address, handler_class)
    print(f"Server started on port {port}")
    httpd.serve_forever()

if __name__ == "__main__":
    run()
